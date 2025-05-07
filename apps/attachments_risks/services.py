from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
# Import the specific risk type
from apps.risks_credit_political.models import CreditPoliticalRisk 
from .models import Attachment
from apps.users.models import User # Import your User model
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings
import uuid
import os

class AttachmentService:
    """Service layer for handling attachment business logic."""

    @staticmethod
    def generate_presigned_upload_url(*, risk_id: uuid.UUID, filename: str, content_type: str, expires_in: int = 3600):
        """
        Generates a pre-signed S3 PUT URL for direct file upload.

        Args:
            risk_id: The UUID of the CreditPoliticalRisk this attachment will belong to.
            filename: The original filename from the client.
            content_type: The MIME type of the file.
            expires_in: Time in seconds for the presigned URL to remain valid.

        Returns:
            A dictionary containing 'url' (the pre-signed URL) and 's3_key' (the S3 object key),
            or None if URL generation fails.
        """
        if not isinstance(risk_id, uuid.UUID):
            raise ValueError("Invalid risk_id (UUID) provided.")

        _, ext = os.path.splitext(filename)
        unique_filename_part = f"{uuid.uuid4()}{ext}"
        # Construct S3 key similar to risk_attachment_path in models.py
        # Note: risk_class_slug is hardcoded as 'credit-political'
        s3_key = f'risks/credit-political/{str(risk_id)}/{unique_filename_part}'

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4') # Recommended for presigned URLs
        )
        try:
            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': s3_key,
                    'ContentType': content_type,
                    # Consider adding 'ACL': 'private' or other ACLs if your bucket isn't private by default
                    # and you don't want these files to be public.
                    # However, with AWS_DEFAULT_ACL = None and AWS_QUERYSTRING_AUTH = False,
                    # access is typically controlled by IAM policies and bucket policies.
                },
                ExpiresIn=expires_in,
                HttpMethod='PUT'
            )
            return {'url': presigned_url, 's3_key': s3_key}
        except ClientError as e:
            # Log this error appropriately
            print(f"Error generating presigned URL: {e}")
            return None

    @staticmethod
    @transaction.atomic
    def create_attachment(*,
                          risk: CreditPoliticalRisk,
                          s3_key: str, # Changed from file: UploadedFile
                          original_filename: str, # Added
                          content_type: str, # Added
                          uploaded_by: User,
                          description: str = None) -> Attachment:
        """
        Creates an Attachment record after a file has been directly uploaded to S3.

        Args:
            risk: The CreditPoliticalRisk instance to associate the attachment with.
            s3_key: The S3 object key (path within the bucket).
            original_filename: The original name of the uploaded file.
            content_type: The MIME type of the uploaded file.
            uploaded_by: The User instance who uploaded the file.
            description: Optional description for the attachment.

        Returns:
            The newly created Attachment instance.
        """
        if not isinstance(risk, CreditPoliticalRisk):
            raise ValueError("Invalid CreditPoliticalRisk object provided.")
        if not s3_key or not isinstance(s3_key, str):
            raise ValueError("Invalid s3_key provided.")
        if not original_filename or not isinstance(original_filename, str):
            raise ValueError("Invalid original_filename provided.")
        if not content_type or not isinstance(content_type, str):
            raise ValueError("Invalid content_type provided.")
        if not isinstance(uploaded_by, User): # Assuming User model is imported
            raise ValueError("Invalid User object provided.")

        attachment = Attachment.objects.create(
            risk=risk,
            # Store the S3 key directly. Django's FileField will store this string.
            # When accessing attachment.file.url, django-storages will construct the full S3 URL.
            file=s3_key,
            uploaded_by=uploaded_by,
            original_filename=original_filename,
            description=description,
            content_type=content_type,
        )
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