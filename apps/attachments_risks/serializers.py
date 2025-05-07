from rest_framework import serializers
from .models import Attachment
# Use the existing UserListSerializer from the users app
from apps.users.serializers import UserListSerializer
import boto3
from botocore.exceptions import ClientError
from django.conf import settings # To access AWS settings

class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for the Attachment model."""
    # Make file read-only in responses, as we handle upload separately
    file_url = serializers.SerializerMethodField()
    # Use UserListSerializer to represent the uploader
    uploaded_by = UserListSerializer(read_only=True)
    # Add risk_id field for associating uploads in requests
    risk_id = serializers.UUIDField(write_only=True, source='risk.id')

    class Meta:
        model = Attachment
        fields = [
            'id', 
            'risk_id', # For associating on create/update (write-only)
            'file_url', # Read-only URL for GET requests
            'original_filename', 
            'description',
            'content_type',
            'uploaded_at',
            'uploaded_by'
        ]
        read_only_fields = [
            'id', 
            'original_filename',
            'content_type',
            'uploaded_at', 
            'uploaded_by',
            'file_url'
        ]
        # Note: 'file' field itself is excluded, we handle it in the view/service

    def get_file_url(self, obj):
        """Generate a pre-signed URL for downloading the file from S3."""
        if obj.file and hasattr(obj.file, 'name') and obj.file.name:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                config=boto3.session.Config(signature_version=settings.AWS_S3_SIGNATURE_VERSION) # e.g., 's3v4'
            )
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            object_key = obj.file.name # This is the S3 key

            try:
                # Generate a pre-signed URL for GET request, valid for 1 hour (3600 seconds)
                # You can adjust the expiration time as needed.
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': object_key},
                    ExpiresIn=3600  # URL expiration in seconds
                )
                return url
            except ClientError as e:
                print(f"Error generating pre-signed URL for {object_key}: {e}")
                return None # Or some error indicator
        return None

class AttachmentUploadSerializer(serializers.Serializer):
    """Serializer specifically for validating file uploads."""
    file = serializers.FileField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    # No model linkage here, just validation for the raw upload data 

class AttachmentPresignedURLRequestSerializer(serializers.Serializer):
    """Serializer for requesting a pre-signed URL for S3 direct upload."""
    filename = serializers.CharField(required=True, max_length=255)
    content_type = serializers.CharField(required=True, max_length=100)
    # risk_id is needed to construct the S3 path if path includes risk_id
    # and to associate during confirmation, but for request, only filename/type
    # if we want to scope the presigned URL to a specific risk_id path,
    # we might need risk_id here. For now, assuming S3 key generated in service.

class AttachmentConfirmUploadSerializer(serializers.Serializer):
    """
    Serializer for confirming a direct S3 upload and creating the Attachment record.
    The client sends this data after the file is successfully uploaded to S3.
    """
    s3_key = serializers.CharField(required=True) # The key (path) of the object in S3
    original_filename = serializers.CharField(required=True, max_length=255)
    content_type = serializers.CharField(required=True, max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    # risk_id will be passed in the URL for the confirmation endpoint,
    # so it's not strictly needed in the body here, but can be included for explicitness if preferred.

    # No model linkage here, just validation for the raw upload data 