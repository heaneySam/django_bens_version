"""
apps/risks_credit_political/serializers.py

Serializer for CreditPoliticalRisk, specifying inherited and class-specific fields.
"""
from rest_framework import serializers
from .models import CreditPoliticalRisk


class CreditPoliticalRiskSerializer(serializers.ModelSerializer):
    """Serializer for credit & political risk objects."""
    class Meta:
        model = CreditPoliticalRisk
        # Include inherited fields from RiskBase and new specific fields
        fields = [
            'id', 'name', 'description', 'created_by', 'created_at', 'updated_at', # Inherited
            'unstructured_data', 'insured', 'country_of_insured', 'counterparty',
            'country_of_counterparty', 'product', 'country_of_risk',
            'creation_date', 'inception_date', 'expiry_date', 'status', 'score' # New fields
            # 'credit_score', # Removed
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at'] 