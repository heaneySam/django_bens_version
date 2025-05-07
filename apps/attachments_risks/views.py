from django.shortcuts import render
from rest_framework import viewsets, status, parsers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction # For atomicity if needed in view, though service handles it
from django.http import Http404 # Import Http404

# Import the specific risk type
from apps.risks_credit_political.models import CreditPoliticalRisk
from .models import Attachment
# Updated Serializer imports
from .serializers import AttachmentSerializer, AttachmentConfirmUploadSerializer, AttachmentPresignedURLRequestSerializer
from .services import AttachmentService
import uuid # For type hinting risk_pk if desired

class RiskAttachmentViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing attachments associated with a specific CreditPoliticalRisk.
    - POST to /generate-upload-url/ to get a pre-signed S3 URL.
    - POST to / (collection) to confirm an upload and create the attachment record.
    - GET to / to list attachments.
    - GET to /{attachment_pk}/ to retrieve a specific attachment.
    """
    serializer_class = AttachmentSerializer # Default for list/retrieve
    permission_classes = [IsAuthenticated]
    # Parsers are generally for incoming request data.
    # generate_presigned_url and confirm (create) will expect JSON.
    # If any future methods (e.g. an update that takes a file) need MultiPartParser,
    # they can declare it using @action(parser_classes=[MultiPartParser])
    # For now, removing from class level. Default is JSONParser.

    def get_queryset(self):
        risk_pk_from_kwarg = self.kwargs.get('risk_pk')
        
        if not isinstance(risk_pk_from_kwarg, uuid.UUID):
            # This implies the URL kwarg 'risk_pk' is missing, not a UUID object
            # (e.g., URL pattern doesn't use <uuid:risk_pk>), or is None.
            return Attachment.objects.none()

        risk_uuid = risk_pk_from_kwarg # It's already a UUID object
        
        try:
            # Ensure the risk actually exists
            risk = get_object_or_404(CreditPoliticalRisk, pk=risk_uuid)
        except Http404: # Django's get_object_or_404 raises Http404
            return Attachment.objects.none()
        
        return AttachmentService.get_attachments_for_risk(risk=risk)

    def list(self, request, risk_pk=None):
        """Lists attachments for a specific risk."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='generate-upload-url')
    def generate_presigned_url(self, request, risk_pk=None):
        """
        Generates a pre-signed S3 PUT URL for direct client-side file upload.
        Expects 'filename' and 'content_type' in the request body.
        The 'risk_pk' is taken from the URL.
        """
        request_serializer = AttachmentPresignedURLRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        
        validated_data = request_serializer.validated_data
        filename = validated_data.get('filename')
        content_type = validated_data.get('content_type')

        # risk_pk parameter comes from the URL, potentially already a UUID object
        if not isinstance(risk_pk, uuid.UUID):
            return Response({"error": "Invalid risk_pk format or type."}, status=status.HTTP_400_BAD_REQUEST)
        
        risk_uuid = risk_pk # Use directly

        # Optional: ensure risk exists (can be done by service or here)
        # try:
        #     get_object_or_404(CreditPoliticalRisk, pk=risk_uuid)
        # except Http404:
        #     return Response({"error": "Risk not found."}, status=status.HTTP_404_NOT_FOUND)

        presigned_data = AttachmentService.generate_presigned_upload_url(
            risk_id=risk_uuid, # Pass the UUID object
            filename=filename,
            content_type=content_type
        )

        if presigned_data:
            return Response(presigned_data, status=status.HTTP_200_OK)
        else:
            # Log error details from service if possible
            return Response({"error": "Failed to generate pre-signed URL."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # This 'create' method now CONFIRMS the upload and creates the DB record.
    # It's triggered by POST to /api/risks/credit-political/{risk_pk}/attachments/
    def create(self, request, risk_pk=None):
        """
        Confirms a direct S3 upload and creates the Attachment database record.
        Expects 's3_key', 'original_filename', 'content_type', and optionally 'description'.
        """
        # risk_pk parameter comes from the URL, potentially already a UUID object
        if not isinstance(risk_pk, uuid.UUID):
            return Response({"error": "Invalid risk_pk format or type."}, status=status.HTTP_400_BAD_REQUEST)
        
        risk_uuid = risk_pk # Use directly

        try:
            risk = get_object_or_404(CreditPoliticalRisk, pk=risk_uuid)
        except Http404:
            return Response({"error": "Risk not found."}, status=status.HTTP_404_NOT_FOUND)

        confirm_serializer = AttachmentConfirmUploadSerializer(data=request.data)
        confirm_serializer.is_valid(raise_exception=True)
        
        validated_data = confirm_serializer.validated_data
        s3_key = validated_data.get('s3_key')
        original_filename = validated_data.get('original_filename')
        content_type = validated_data.get('content_type')
        description = validated_data.get('description')

        try:
            # Using @transaction.atomic in the service layer is preferred
            attachment = AttachmentService.create_attachment(
                risk=risk,
                s3_key=s3_key,
                original_filename=original_filename,
                content_type=content_type,
                uploaded_by=request.user,
                description=description
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e: # Catch other potential errors
            # Log the full exception e for debugging
            print(f"Error creating attachment record: {e}")
            return Response({"error": "Failed to create attachment record after S3 upload."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Use the main serializer for the response
        response_serializer = self.get_serializer(attachment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None, risk_pk=None):
        """Retrieves a specific attachment."""
        try:
            # Ensure pk for attachment is a valid UUID string and convert
            # (assuming URL pattern for 'pk' is <str:pk> or not type-converted to UUID)
            attachment_uuid = uuid.UUID(str(pk))
        except (ValueError, TypeError): # Catch if pk is None or not a valid UUID string
            return Response({"error": "Invalid attachment ID format."}, status=status.HTTP_400_BAD_REQUEST)
            
        # self.kwargs['risk_pk'] will be used by get_queryset if risk_pk method arg is None.
        # Ensure risk_pk (from URL for parent risk) is correctly passed to get_queryset context
        # If risk_pk is a method argument, it's already a UUID (if <uuid:risk_pk> in URL)
        # If get_queryset relies on self.kwargs.get('risk_pk'), that's handled by get_queryset.
        # No specific change needed for risk_pk here as get_queryset handles it.
            
        attachment_qs = self.get_queryset()
        if not attachment_qs.exists() and attachment_qs.model.objects.none().all().count() == 0 and self.kwargs.get('risk_pk') is None : # check if get_queryset returned none due to missing risk_pk
             # This check is a bit complex; primary goal is get_object_or_404 on correctly filtered qs
             pass


        attachment = get_object_or_404(attachment_qs, pk=attachment_uuid)
        serializer = self.get_serializer(attachment)
        return Response(serializer.data)

    # Add destroy method later if needed.
    # Remember: if you add destroy, it must also delete the object from S3.
    # This typically involves using boto3 to call s3_client.delete_object(...)
    # and should probably be encapsulated in AttachmentService.
