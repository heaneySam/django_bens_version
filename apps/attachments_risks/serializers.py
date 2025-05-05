from rest_framework import serializers
from .models import Attachment
# Use the existing UserListSerializer from the users app
from apps.users.serializers import UserListSerializer

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
        """Return the public URL for the file stored in S3."""
        if obj.file:
            return obj.file.url
        return None

class AttachmentUploadSerializer(serializers.Serializer):
    """Serializer specifically for validating file uploads."""
    file = serializers.FileField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)

    # No model linkage here, just validation for the raw upload data 