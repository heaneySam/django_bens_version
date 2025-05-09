# apps/guidelines/serializers.py

from rest_framework import serializers
from .models import Guideline, Trust
from django.core.files.storage import default_storage
# from .utils import sanitize_filename, get_s3_key
import logging
import os
import re

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
    # Add other allowed MIME types if necessary
]
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB



class TrustSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trust
        fields = ['id', 'name']  # Include other Trust fields if necessary


class GuidelineMinimalSerializer(serializers.ModelSerializer):
    # trust = TrustSerializer(read_only=True)

    class Meta:
        model = Guideline
        fields = [
            'id',
            # 'trust',
            'name',
            'external_url',
            'description',
            'viewcount',
            'medical_speciality',
        ]

class GuidelineAdminSerializer(serializers.ModelSerializer):
    # trust = TrustSerializer(read_only=True)

    class Meta:
        model = Guideline
        fields = [
            'id',
            # 'trust',
            'name',
            'description',
            'medical_speciality',
            'external_url',
            'review_date',
            'last_updated_date',
        ]



class GuidelineSerializer(serializers.ModelSerializer):
    trust = TrustSerializer(read_only=True)
    # pdf_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Guideline
        fields = [
            'id',
            'trust',
            'name',
            'description',
            'external_url',
            'metadata',
            'medical_speciality',
            'locality',
            'original_filename',
            'viewcount',
            'version_number',
            'authors',
            'creation_date',
            'review_date',
        ]
        read_only_fields = ['viewcount']
        extra_kwargs = {
            'description': {'required': False},
            'external_url': {'required': False},
            'metadata': {'required': False},
            'medical_speciality': {'required': False},
            'locality': {'required': False},
            'original_filename': {'required': False},
            'version_number': {'required': False},
            'authors': {'required': False},
            'creation_date': {'required': False},
            'review_date': {'required': False},
        }


class UploadPDFSerializer(serializers.Serializer):
    """
    A minimal serializer for uploading a new PDF and updating the external_url.
    """
    pdf_file = serializers.FileField(required=True)
    # optionally let them provide a 'filename' or 'versioning' approach
    # name = serializers.CharField(required=False)
    # version_increment = serializers.BooleanField(default=True)

    def validate_pdf_file(self, value):
        # Validate file type
        if value.content_type not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError("Unsupported file type. Only PDF and DOCX are allowed.")

        # Validate file size
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("File size exceeds the maximum limit of 50MB.")

        return value


    def update(self, instance, validated_data):
        pdf_file = validated_data["pdf_file"]
        old_url = instance.external_url
        logger.debug(f"Starting PDF upload for TrustGuideline ID {instance.id}")
        sanitized_name = sanitize_filename(pdf_file.name)
        logger.debug(f"Sanitized file name: {sanitized_name}")
        if instance.version_number.isdigit():
            current_version = int(instance.version_number)
        else:
            current_version = 0
        new_version = current_version + 1

        logger.debug(f"Incremented version number: {new_version}")

        # Update the version number in the instance
        instance.version_number = str(new_version)

        # Define the new file name with versioning
        base_name, ext = os.path.splitext(sanitized_name)
        file_name = f"{base_name}_v{new_version}{ext}"
        file_path = f"guidelines/{instance.id}/{file_name}"

        logger.debug(f"File path for upload: {file_path}")

        try:
            # If an old URL exists, delete the old file from S3
            if old_url:
                old_key = get_s3_key(old_url)
                logger.debug(f"Attempting to delete old S3 object: {old_key}")
                if default_storage.exists(old_key):
                    default_storage.delete(old_key)
                    logger.info(f"Deleted old S3 object: {old_key}")
                else:
                    logger.warning(f"Old S3 object does not exist: {old_key}")

            # Save the new file to S3
            saved_path = default_storage.save(file_path, pdf_file)
            new_url = default_storage.url(saved_path)

            logger.info(f"Uploaded new PDF to {new_url}")

            # Update instance fields
            instance.external_url = new_url
            instance.original_filename = pdf_file.name  # Optionally keep the original filename

        except Exception as e:
            logger.error(f"Error uploading PDF for TrustGuideline ID {instance.id}: {e}")
            raise serializers.ValidationError(f"Failed to upload PDF: {e}")
        
        instance.save()
        logger.debug(f"Updated TrustGuideline ID {instance.id} with new external_url")
        return instance
