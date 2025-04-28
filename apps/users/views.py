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
from .serializers import RequestMagicLinkSerializer # Need these serializers
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.contrib.auth import login as django_login
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator

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

@method_decorator(csrf_exempt, name='dispatch')
class RequestMagicLinkView(APIView):
    """
    API endpoint to request a magic login link (MagicLink).
    Uses allauth's user management internally.
    """
    permission_classes = [AllowAny]
    serializer_class = RequestMagicLinkSerializer

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
        logger.debug("RequestMagicLinkView POST data: %s", request.data)
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
                # Create a MagicLink and build backend confirmation URL
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
            logger.warning("RequestMagicLinkSerializer errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ConfirmMagicLinkView: DRF-powered HTML GET form + JSON POST
@method_decorator(csrf_exempt, name='dispatch')
class ConfirmMagicLinkView(APIView):
    # Skip DRF SessionAuthentication to avoid CSRF checks here
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes     = [FormParser, JSONParser]
    renderer_classes   = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request, *args, **kwargs):
        # Debug: log incoming token and cookies
        token = request.GET.get('token')
        logger.debug("ConfirmMagicLinkView GET called. token=%s", token)
        logger.debug("Incoming request cookies: %s", request.COOKIES)
        # Validate magic link and issue JWT tokens as cookies
        try:
            magic_link = MagicLink.objects.get(token=token)
        except MagicLink.DoesNotExist:
            return redirect(f"{settings.FRONTEND_URL}/?error=invalid_link")
        expiry = magic_link.created_at + timedelta(minutes=settings.MAGIC_LINK_EXPIRY_MINUTES)
        if timezone.now() > expiry or magic_link.used:
            return redirect(f"{settings.FRONTEND_URL}/?error=expired_link")
        magic_link.used = True
        magic_link.save()
        user = magic_link.user
        # Issue JWT tokens for the user
        refresh = RefreshToken.for_user(user)
        logger.debug("Issuing JWT tokens for user %s: access=%s refresh=%s", user.pk, refresh.access_token, refresh)
        # Redirect to front-end with tokens set as HTTP-only cookies
        response = HttpResponseRedirect(f"{settings.FRONTEND_URL}/?logged_in=1")
        # Debug: list all Set-Cookie headers before sending
        for name, morsel in response.cookies.items():
            logger.debug("Set-Cookie header: %s", morsel.OutputString())
        # Determine cookie security and sameSite based on environment
        secure_cookie = not settings.DEBUG
        samesite_mode = 'None' if secure_cookie else 'Lax'
        # Set JWT cookies; in dev use Lax samesite over HTTP, in prod allow None with Secure
        response.set_cookie(
            'access_token',
            str(refresh.access_token),
            httponly=True,
            secure=secure_cookie,
            samesite=samesite_mode,
            path='/'
        )
        response.set_cookie(
            'refresh_token',
            str(refresh),
            httponly=True,
            secure=secure_cookie,
            samesite=samesite_mode,
            path='/'
        )
        return response

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
        # Log in the user via Django session and return user info
        user = magic_link.user
        # Log in via AllAuth session backend
        django_login(request._request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
        return Response({
            "success": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }, status=status.HTTP_200_OK)

# Add session endpoint to return current authenticated user
class SessionView(APIView):
    """
    API endpoint to retrieve the current user session (authenticated user info).
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Debug: inspect incoming cookies and header
        logger.debug("SessionView GET called. cookies=%s HTTP_COOKIE=%s", request.COOKIES, request.META.get('HTTP_COOKIE'))
        user = request.user
        logger.debug("SessionView authentication status: user.is_authenticated=%s", user.is_authenticated)
        if user.is_authenticated:
            return Response({
                'user': {
                    'id': str(user.id),
                    'email': user.email
                }
            })
        return Response({'user': None})

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFCookieView(APIView):
    """
    API endpoint that ensures CSRF cookie is set.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Simply return a 200 so that the CSRF token cookie is set
        return Response({"detail": "CSRF cookie set"}, status=status.HTTP_200_OK)
