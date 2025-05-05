"""
apps/risks_credit_political/serializers.py

Serializer for CreditPoliticalRisk, specifying inherited and class-specific fields.
"""
from rest_framework import serializers
from apps.attachments_risks.models import Attachment
from .models import CreditPoliticalRisk


class CreditPoliticalRiskSerializer(serializers.ModelSerializer):
    """Serializer for credit & political risk objects."""
    # Add a field to compute the attachment count
    attachments_count = serializers.SerializerMethodField()

    class Meta:
        model = CreditPoliticalRisk
        # Include inherited fields from RiskBase and new specific fields
        fields = [
            'id', 'name', 'description', 'created_by', 'created_at', 'updated_at', # Inherited
            'unstructured_data', 'insured', 'country_of_insured', 'counterparty',
            'country_of_counterparty', 'product', 'country_of_risk',
            'creation_date', 'inception_date', 'expiry_date', 'status', 'score', # Existing specific fields
            'source_system', 'source_record_id', # Added integration fields
            'attachments_count' # Add the new computed field
            # 'credit_score', # Removed
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_attachments_count(self, obj: CreditPoliticalRisk) -> int:
        """Calculates the number of attachments linked directly via the ForeignKey."""
        # Use the reverse relation 'attachments' defined in the Attachment model
        return obj.attachments.count()

    # Removed the old implementation using ContentType
    # def get_attachments_count(self, obj: CreditPoliticalRisk) -> int:
    #     """Calculates the number of attachments linked to this risk instance."""
    #     try:
    #         # Get the ContentType for the CreditPoliticalRisk model
    #         content_type = ContentType.objects.get_for_model(obj)
    #         # Count attachments associated with this specific risk object
    #         count = Attachment.objects.filter(content_type=content_type, object_id=obj.pk).count()
    #         return count
    #     except ContentType.DoesNotExist:
    #         # Should not happen if migrations are correct, but handle defensively
    #         return 0
    #     except Exception as e:
    #         # Log the error e
    #         print(f"Error calculating attachment count for {obj}: {e}")
    #         return 0 # Return 0 on error to avoid breaking serialization 