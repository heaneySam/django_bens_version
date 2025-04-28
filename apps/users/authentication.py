from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that extracts the access token from an HTTP-only cookie instead of the Authorization header.
    """
    def authenticate(self, request):
        # Retrieve the access token from the 'access_token' cookie
        raw_token = request.COOKIES.get('access_token')
        logger.debug("CookieJWTAuthentication.authenticate raw_token=%s", raw_token)
        if not raw_token:
            return None
        try:
            # Validate token
            validated_token = self.get_validated_token(raw_token)
            # Load user
            user = self.get_user(validated_token)
            logger.debug("CookieJWTAuthentication: token valid for user %s", user.pk)
            return (user, validated_token)
        except Exception as e:
            # Token is missing, expired, or invalid => treat as unauthenticated
            logger.debug("CookieJWTAuthentication: invalid or expired token, ignoring. error=%s", e)
            return None 