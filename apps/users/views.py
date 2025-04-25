from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserListSerializer
import logging
import inspect
from django.urls import get_resolver, reverse

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
                flows.login_by_code.LoginCodeVerificationProcess.initiate(
                    request=request._request,
                    user=user,
                    email=email
                )
                logger.info("Login code initiated for %s", email)
                return Response({"detail": "Login code requested. Check your console/email."}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.exception("Exception during login code initiation for %s", email)
                return Response({"detail": "Failed to process login code request."}, status=status.HTTP_400_BAD_REQUEST)
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
