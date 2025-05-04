"""
apps/risks_directors_officers/services.py

Service layer for DirectorsOfficersRisk operations.
All ORM calls are centralized here for testability and separation from HTTP.
"""
from .models import DirectorsOfficersRisk

class DirectorsOfficersRiskService:
    """Service for Directors & Officers risk CRUD operations."""

    @staticmethod
    def list_risks():
        """Return a queryset of all DirectorsOfficersRisk objects."""
        return DirectorsOfficersRisk.objects.all()

    @staticmethod
    def get_risk(pk):
        """Retrieve a DirectorsOfficersRisk by primary key (raises if not found)."""
        return DirectorsOfficersRisk.objects.get(pk=pk)

    @staticmethod
    def create_risk(validated_data, created_by):
        """
        Create and return a new DirectorsOfficersRisk.
        :param validated_data: dict of serializer.validated_data (excluding created_by)
        :param created_by: User instance creating the risk
        """
        return DirectorsOfficersRisk.objects.create(created_by=created_by, **validated_data)

    @staticmethod
    def update_risk(risk, validated_data):
        """
        Update an existing DirectorsOfficersRisk with validated_data and return it.
        :param risk: DirectorsOfficersRisk instance to update
        :param validated_data: dict of fields to update
        """
        for attr, value in validated_data.items():
            setattr(risk, attr, value)
        risk.save(update_fields=list(validated_data.keys()))
        return risk

    @staticmethod
    def delete_risk(risk):
        """Delete a DirectorsOfficersRisk instance from the database."""
        risk.delete() 