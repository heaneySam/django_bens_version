from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, MagicLink


class UserService:
    """
    Service for user-related business logic.
    """
    @staticmethod
    def get_or_create_user_by_email(email):
        """
        Retrieve an existing user by email or create a new one.
        """
        user, _ = User.objects.get_or_create(
            username=email,
            defaults={'email': email}
        )
        return user


class MagicLinkService:
    """
    Service for magic link creation and verification.
    """
    class InvalidMagicLink(Exception):
        """Raised when a magic link token is invalid."""
        pass

    class ExpiredMagicLink(Exception):
        """Raised when a magic link token is expired or already used."""
        pass

    @staticmethod
    def create_magic_link(user):
        """
        Create a new magic link for the user.
        """
        return MagicLink.objects.create(user=user)

    @staticmethod
    def build_confirm_url(token, request):
        """
        Construct the magic link confirmation URL.
        """
        return f"{request.scheme}://{request.get_host()}/api/auth/magic/confirm/?token={token}"

    @staticmethod
    def send_magic_link_email(user, confirm_url):
        """
        Send the magic link email to the user.
        """
        print(f"[DEBUG] send_magic_link_email called with user: {user} (email: {getattr(user, 'email', None)})")
        print(f"[DEBUG] send_magic_link_email called with confirm_url: {confirm_url}")
        site = Site.objects.get_current()
        context = {
            'site_name': site.name,
            'site_domain': site.domain,
            'magic_link_url': confirm_url,
            'expiry_minutes': settings.MAGIC_LINK_EXPIRY_MINUTES,
            'user': user,
        }
        subject = render_to_string('account/email/magic_link_subject.txt', context).strip()
        message = render_to_string('account/email/magic_link_message.txt', context)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

    @staticmethod
    def confirm_magic_link_and_issue_tokens(token):
        """
        Verify a magic link token, consume it, and issue JWT tokens.
        Returns a dict with 'access_token' and 'refresh_token'.
        """
        try:
            magic_link = MagicLink.objects.get(token=token)
        except MagicLink.DoesNotExist:
            raise MagicLinkService.InvalidMagicLink

        expiry = magic_link.created_at + timedelta(minutes=settings.MAGIC_LINK_EXPIRY_MINUTES)
        if timezone.now() > expiry or magic_link.used:
            raise MagicLinkService.ExpiredMagicLink

        magic_link.used = True
        magic_link.save()

        # Issue JWT tokens
        refresh = RefreshToken.for_user(magic_link.user)
        return {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
        }


class TokenService:
    """
    Service for JWT token issuance, refresh, and blacklisting.
    """
    class InvalidToken(Exception):
        """Raised when a provided token is invalid."""
        pass

    @staticmethod
    def refresh_access_token(refresh_token_str):
        """
        Validate and refresh the access token using a refresh token string.
        """
        try:
            refresh = RefreshToken(refresh_token_str)
        except Exception:
            raise TokenService.InvalidToken

        new_access = str(refresh.access_token)
        return new_access

    @staticmethod
    def blacklist_refresh_token(refresh_token_str):
        """
        Blacklist the provided refresh token.
        """
        refresh = RefreshToken(refresh_token_str)
        refresh.blacklist() 