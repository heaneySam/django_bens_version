from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
# Import the specific risk type
from apps.risks_credit_political.models import CreditPoliticalRisk 
from .models import Attachment
from apps.users.models import User # Import your User model

class AttachmentService:
    """Service layer for handling attachment business logic."""

    @staticmethod
    @transaction.atomic
    def create_attachment(*, risk: CreditPoliticalRisk, file: UploadedFile, uploaded_by: User, description: str = None) -> Attachment:
        """
        Creates an Attachment record and saves the file to storage.

        Args:
            risk: The CreditPoliticalRisk instance to associate the attachment with.
            file: The UploadedFile object from the request.
            uploaded_by: The User instance who uploaded the file.
            description: Optional description for the attachment.

        Returns:
            The newly created Attachment instance.
        """
        # Basic validation (can add more specific checks)
        if not isinstance(risk, CreditPoliticalRisk):
            raise ValueError("Invalid CreditPoliticalRisk object provided.")
        if not isinstance(file, UploadedFile):
            raise ValueError("Invalid file object provided.")
        if not isinstance(uploaded_by, User):
            raise ValueError("Invalid User object provided.")

        # Create the attachment instance
        # The FileField's save method handles moving the file to S3 via upload_to
        attachment = Attachment.objects.create(
            risk=risk,
            file=file, # Django handles saving the file content here
            uploaded_by=uploaded_by,
            original_filename=file.name,
            description=description,
            content_type=file.content_type,
        )
        # Note: The file is saved to S3 when Attachment.objects.create() is called
        # because the FileField handles it.

        return attachment

    @staticmethod
    def get_attachments_for_risk(*, risk: CreditPoliticalRisk):
        """Retrieves all attachments for a given CreditPoliticalRisk."""
        if not isinstance(risk, CreditPoliticalRisk):
            raise ValueError("Invalid CreditPoliticalRisk object provided.")
        return Attachment.objects.filter(risk=risk).select_related('uploaded_by')

    # Potential future methods:
    # - delete_attachment(attachment_id, user) -> handles permissions, deletes DB record & S3 object
    # - update_attachment_description(attachment_id, description, user) -> handles permissions

    # ... rest of the original file content ... 