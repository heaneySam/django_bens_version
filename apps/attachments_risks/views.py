from django.shortcuts import render
from rest_framework import viewsets, status, parsers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

# Import the specific risk type
from apps.risks_credit_political.models import CreditPoliticalRisk
from .models import Attachment # Import Risk model
from .serializers import AttachmentSerializer, AttachmentUploadSerializer
from .services import AttachmentService

class RiskAttachmentViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing attachments associated with a specific CreditPoliticalRisk.
    Accessed via nested routing like /api/risks/credit-political/{risk_pk}/attachments/
    """
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser] # Handle file uploads

    # The queryset needs to be dynamic based on the risk_id from the URL
    # We override get_queryset instead of setting a static queryset attribute
    def get_queryset(self):
        risk_id = self.kwargs.get('risk_pk') # Assuming nested router passes risk_pk
        if not risk_id:
            # This shouldn't happen with correctly configured nested routing
            return Attachment.objects.none()
        # Get the specific risk object
        risk = get_object_or_404(CreditPoliticalRisk, pk=risk_id)
        # Ensure the user has access to the risk if necessary (add permission checks here)
        # Example: if risk.created_by != self.request.user: raise PermissionDenied
        return AttachmentService.get_attachments_for_risk(risk=risk)

    def list(self, request, risk_pk=None):
        """Lists attachments for a specific risk.""" 
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, risk_pk=None):
        """Handles file upload and creates an Attachment."""
        # Get the specific risk object
        risk = get_object_or_404(CreditPoliticalRisk, pk=risk_pk)
        # Use the upload serializer to validate the file and description
        upload_serializer = AttachmentUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        file = upload_serializer.validated_data['file']
        description = upload_serializer.validated_data.get('description')

        try:
            attachment = AttachmentService.create_attachment(
                risk=risk,
                file=file,
                uploaded_by=request.user, # Assumes user is authenticated
                description=description
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the exception e
            return Response({"error": "Failed to upload attachment."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Use the main serializer to format the response
        response_serializer = self.get_serializer(attachment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    # Optional: Add retrieve, destroy methods if needed
    def retrieve(self, request, pk=None, risk_pk=None):
        """Retrieves a specific attachment."""
        # get_queryset already filters by risk_pk from the URL
        attachment = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(attachment)
        return Response(serializer.data)

    # Add destroy method later if needed, remember to delete from S3 too!
    # def destroy(self, request, pk=None, risk_pk=None): ...
