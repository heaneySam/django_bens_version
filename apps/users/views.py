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
import os
from rest_framework_simplejwt.exceptions import TokenError

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
                confirm_url = f"{request.scheme}://{request.get_host()}/api/auth/magic/confirm/?token={token}"
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
        # Prepare token payload for proxy use
        token_data = {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
        }
        # If the client expects JSON (proxy), return tokens and skip cookie-setting
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'application/json' in accept_header:
            return Response(token_data, status=status.HTTP_200_OK)
        # Else fall back to HTML flow: set backend-domain cookies and redirect
        response = HttpResponseRedirect(f"{settings.FRONTEND_URL}")
        # Debug: list all Set-Cookie headers before sending
        for name, morsel in response.cookies.items():
            logger.debug("Set-Cookie header: %s", morsel.OutputString())
        # Determine cookie attributes based on environment
        secure_cookie = not settings.DEBUG
        samesite_mode = 'Lax' if settings.DEBUG else 'None'
        cookie_kwargs = {
            'httponly': True,
            'secure': secure_cookie,
            'samesite': samesite_mode,
            'path': '/',
        }
        frontend_domain = os.getenv('FRONTEND_COOKIE_DOMAIN')
        if frontend_domain:
            cookie_kwargs['domain'] = frontend_domain
        # Set JWT cookies with appropriate attributes for HTML clients
        response.set_cookie('access_token', str(refresh.access_token), **cookie_kwargs)
        response.set_cookie('refresh_token', str(refresh), **cookie_kwargs)
        for name, value in response.items():
            logger.debug(f"Response header: {name}: {value}")
        for name, morsel in response.cookies.items():
            logger.debug(f"Set-Cookie header: {morsel.OutputString()}")
        return response

    def post(self, request, *args, **kwargs):
        # Disable JSON POST endpoint; use click-to-login via GET only
        return Response(
            {"detail": "Method not allowed. Please click the magic link in your email."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

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

# Token refresh view to issue new access tokens from refresh_token cookie
@method_decorator(csrf_exempt, name='dispatch')
class TokenRefreshView(APIView):
    """
    API endpoint to refresh JWT access token using the refresh token stored in HttpOnly cookie.
    """
    permission_classes = [AllowAny]

    def initial(self, request, *args, **kwargs):
        # Log entry into the refresh endpoint and incoming cookies
        logger.debug("TokenRefreshView initial, cookies=%s", request.COOKIES)
        return super().initial(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        logger.debug("TokenRefreshView invoked. refresh_token cookie: %s", refresh_token)
        if not refresh_token:
            return Response({"detail": "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(refresh_token)
        except TokenError:
            logger.warning("TokenRefreshView invalid refresh token: %s", refresh_token)
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        access_token = str(refresh.access_token)
        logger.debug("TokenRefreshView issuing new access_token: %s", access_token)
        response = Response({"access_token": access_token}, status=status.HTTP_200_OK)
        # Always use Secure and SameSite=None for cross-site cookie transmission
        secure_cookie = True
        samesite_mode = 'None'
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=secure_cookie,
            samesite=samesite_mode,
            path='/',
        )
        return response

@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFCookieView(APIView):
    """
    API endpoint that ensures CSRF cookie is set.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Simply return a 200 so that the CSRF token cookie is set
        return Response({"detail": "CSRF cookie set"}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    """
    API endpoint to log out the current user by blacklisting the refresh token
    and clearing authentication cookies.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Blacklist the refresh token from the cookie, if present
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.debug("Blacklisted refresh token %s", refresh_token)
            except Exception as e:
                logger.exception("Failed to blacklist refresh token: %s", e)

        # Prepare response and clear cookies on client, using FRONTEND_COOKIE_DOMAIN
        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        # Delete cookies using the same domain they were set (FRONTEND_COOKIE_DOMAIN)
        frontend_cookie_domain = os.getenv('FRONTEND_COOKIE_DOMAIN', None)
        if frontend_cookie_domain:
            response.delete_cookie('access_token', path='/', domain=frontend_cookie_domain)
            response.delete_cookie('refresh_token', path='/', domain=frontend_cookie_domain)
        else:
            # fallback to host-only cookies
            response.delete_cookie('access_token', path='/')
            response.delete_cookie('refresh_token', path='/')
        return response
