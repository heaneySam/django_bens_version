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
from .services import UserService, MagicLinkService, TokenService

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
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            allowed_emails = ["heaney.sam@gmail.com", "heaney.ben@gmail.com"]
            if email.lower() not in [e.lower() for e in allowed_emails]:
                return Response({"detail": "This email is not authorized to log in."}, status=403)

            try:
                user = UserService.get_or_create_user_by_email(email)
                magic_link = MagicLinkService.create_magic_link(user)
                confirm_url = MagicLinkService.build_confirm_url(magic_link.token, request)
                MagicLinkService.send_magic_link_email(user, confirm_url)
                return Response({"detail": "Magic link sent. Check your email."}, status=status.HTTP_200_OK)
            except Exception:
                logger.exception("Failed to create and send magic link for %s", email)
                return Response({"detail": "Failed to create magic link."}, status=status.HTTP_400_BAD_REQUEST)
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
        token = request.GET.get('token')
        try:
            tokens = MagicLinkService.confirm_magic_link_and_issue_tokens(token)
        except MagicLinkService.InvalidMagicLink:
            return redirect(f"{settings.FRONTEND_URL}/?error=invalid_link")
        except MagicLinkService.ExpiredMagicLink:
            return redirect(f"{settings.FRONTEND_URL}/?error=expired_link")

        # JSON client
        accept_header = request.META.get('HTTP_ACCEPT', '')
        if 'application/json' in accept_header:
            return Response(tokens, status=status.HTTP_200_OK)

        # HTML client: set cookies and redirect
        response = HttpResponseRedirect(f"{settings.FRONTEND_URL}")
        secure_cookie = not settings.DEBUG
        samesite_mode = 'Lax' if settings.DEBUG else 'None'
        cookie_kwargs = {
            'httponly': True,
            'secure': secure_cookie,
            'samesite': samesite_mode,
            'path': '/',
            'domain': settings.FRONTEND_COOKIE_DOMAIN,
        }
        response.set_cookie('access_token', tokens['access_token'], **cookie_kwargs)
        response.set_cookie('refresh_token', tokens['refresh_token'], **cookie_kwargs)
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
        if not refresh_token:
            return Response({"detail": "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            new_access = TokenService.refresh_access_token(refresh_token)
        except TokenService.InvalidToken:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"access_token": new_access}, status=status.HTTP_200_OK)
        response.set_cookie(
            'access_token', new_access,
            httponly=True,
            secure=True,
            samesite='None',
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
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                TokenService.blacklist_refresh_token(refresh_token)
            except Exception as e:
                logger.exception("Failed to blacklist refresh token: %s", e)

        response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

        cookie_domain = getattr(settings, 'FRONTEND_COOKIE_DOMAIN', None)

        response.delete_cookie(
            key='access_token',
            path='/',
            domain=cookie_domain
        )
        response.delete_cookie(
            key='refresh_token',
            path='/',
            domain=cookie_domain
        )

        return response