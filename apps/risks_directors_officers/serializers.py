"""
apps/risks_directors_officers/serializers.py

Serializer for DirectorsOfficersRisk, specifying inherited and class-specific fields.
"""
from rest_framework import serializers
from .models import DirectorsOfficersRisk

class DirectorsOfficersRiskSerializer(serializers.ModelSerializer):
    """Serializer for Directors & Officers risk objects."""
    class Meta:
        model = DirectorsOfficersRisk
        fields = [
            'id', 'name', 'description', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
