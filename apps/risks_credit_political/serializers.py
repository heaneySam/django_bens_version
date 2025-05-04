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
        fields = [
            'id', 'name', 'description', 'created_by', 'created_at', 'updated_at',
            'credit_score',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at'] 