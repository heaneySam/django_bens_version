from rest_framework import viewsets, permissions
from .models import User, MagicLink
from .serializers import UserListSerializer
import logging
import inspect
from django.urls import get_resolver, reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.models import Site
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from rest_framework.authtoken.models import Token # Use DRF Token
from allauth.account.internal import flows # Import the flows module
from allauth.account.internal.stagekit import get_pending_stage, clear_login
from .serializers import RequestLoginCodeSerializer, ConfirmLoginCodeSerializer # Need these serializers
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

logger = logging.getLogger(__name__)

# Create your views here.

class UserListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed.
    Restricted to admin users.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser] # Only allow admin users

# --- Magic Link API Views ---

class RequestLoginCodeView(APIView):
    """
    API endpoint to request a magic login code.
    Uses allauth's RequestLoginCodeForm internally.
    """
    permission_classes = [AllowAny]
    serializer_class = RequestLoginCodeSerializer

    def post(self, request, *args, **kwargs):
        # Debug: dump all URL route names and test reversing signup
        url_names = list(get_resolver().reverse_dict.keys())
        logger.debug("Available URL names: %s", url_names)
        if 'account_signup' in url_names:
            try:
                signup_url = reverse('account_signup')
                logger.debug("Reversed 'account_signup' -> %s", signup_url)
            except Exception:
                logger.exception("Failed to reverse 'account_signup'")
        else:
            logger.warning("'account_signup' not found in URL names; signup link reverse will fail")
        logger.debug("RequestLoginCodeView POST data: %s", request.data)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            # Ensure a user exists (create on the fly if needed)
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(username=email, email=email)
            logger.debug("Using user %r for magic link initiation", user)
            # Log signature and inputs for debugging
            logger.debug("Initiate signature: %s", inspect.signature(flows.login_by_code.LoginCodeVerificationProcess.initiate))
            logger.debug("Initiating login-by-code: user=%r, email=%s", user, email)
            try:
                # Create and send a MagicLink
                magic_link = MagicLink.objects.create(user=user)
                token = magic_link.token
                confirm_path = reverse('confirm_magic_link')
                confirm_url = request.build_absolute_uri(f"{confirm_path}?token={token}")
                site = Site.objects.get_current()
                email_context = {
                    'site_name': site.name,
                    'site_domain': site.domain,
                    'magic_link_url': confirm_url,
                    'expiry_minutes': settings.MAGIC_LINK_EXPIRY_MINUTES,
                    'user': user,
                }
                subject = render_to_string('account/email/magic_link_subject.txt', email_context).strip()
                message = render_to_string('account/email/magic_link_message.txt', email_context)
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                logger.info("Magic link sent to %s", email)
                return Response({"detail": "Magic link sent. Check your email."}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.exception("Exception during magic link creation for %s", email)
                return Response({"detail": "Failed to create magic link."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning("RequestLoginCodeSerializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConfirmLoginCodeView(APIView):
    """
    API endpoint to confirm a magic login code and get an auth token.
    Uses allauth's ConfirmLoginCodeForm internally.
    """
    permission_classes = [AllowAny]
    serializer_class = ConfirmLoginCodeSerializer

    def post(self, request, *args, **kwargs):
        # Debug URL names again before confirmation
        url_names = list(get_resolver().reverse_dict.keys())
        logger.debug("Available URL names at confirm: %s", url_names)
        logger.debug("ConfirmLoginCodeView POST data: %s", request.data)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            logger.debug("Resuming login-by-code: email=%s, code=%s", email, code)
            # Resume and complete the login-by-code flow
            # Retrieve the pending login stage from the session
            stage = get_pending_stage(request._request)
            if not stage:
                logger.error("No login code process in progress for %s", email)
                return Response({"detail": "No login code process in progress."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                process = flows.login_by_code.LoginCodeVerificationProcess.resume(stage)
                logger.debug("Process resumed: %r", process)
                if not process:
                    logger.error("No login code process in progress for %s", email)
                    return Response({"detail": "No login code process in progress."}, status=status.HTTP_400_BAD_REQUEST)
                logger.debug("Process state before confirm: %s", process.state)
                # Verify the one-time code against the stored state
                if code != process.code:
                    logger.warning("Invalid or expired code for %s", email)
                    return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)
                # Clear the pending login/session state
                clear_login(request._request)
                # Issue a DRF auth token for the user
                user = process.user
                token, created = Token.objects.get_or_create(user=user)
                logger.info("Authenticated user %s via magic code, token created=%s", user.pk, created)
                return Response({"key": token.key}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.exception("Exception during code confirmation for %s", email)
                return Response({"detail": "Internal error during code confirmation."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("ConfirmLoginCodeSerializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ConfirmMagicLinkView: DRF-powered HTML GET form + JSON POST
class ConfirmMagicLinkView(APIView):
    """
    API view to confirm magic link tokens: renders HTML form on GET, returns JWT JSON on POST.
    Use ?format=json on POST to select JSONRenderer automatically.
    """
    permission_classes = [AllowAny]
    parser_classes     = [FormParser, JSONParser]
    renderer_classes   = [TemplateHTMLRenderer, JSONRenderer]

    def get_renderers(self):
        # Force JSON on POST (for token response) and HTML on GET (for form)
        if self.request.method == 'POST':
            return [JSONRenderer()]
        return [TemplateHTMLRenderer()]

    def get(self, request, *args, **kwargs):
        token = request.GET.get('token')
        logger.debug("ConfirmMagicLinkView GET token=%s", token)
        # Validate link existence and expiry
        try:
            magic_link = MagicLink.objects.get(token=token)
        except MagicLink.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, template_name='users/magic_link_invalid.html')
        expiry = magic_link.created_at + timedelta(minutes=settings.MAGIC_LINK_EXPIRY_MINUTES)
        if timezone.now() > expiry or magic_link.used:
            return Response(status=status.HTTP_400_BAD_REQUEST, template_name='users/magic_link_invalid.html')
        # Render the confirmation form
        context = {
            'token': token,
            'confirm_url': request.build_absolute_uri(),
        }
        return Response(context, template_name='users/magic_link_confirm.html')

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        logger.debug("ConfirmMagicLinkView POST token=%s", token)
        # Validate & consume token
        try:
            magic_link = MagicLink.objects.get(token=token)
        except MagicLink.DoesNotExist:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        expiry = magic_link.created_at + timedelta(minutes=settings.MAGIC_LINK_EXPIRY_MINUTES)
        if timezone.now() > expiry or magic_link.used:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        magic_link.used = True
        magic_link.save()
        # Issue JWT tokens
        refresh = RefreshToken.for_user(magic_link.user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)
