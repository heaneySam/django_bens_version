"""
apps/risks_directors_officers/models.py

Concrete model for Directors & Officers Risks.
Inherits shared fields from RiskBase; add domain-specific fields here.
"""
from django.db import models
from apps.risks_core.models import RiskBase


class DirectorsOfficersRisk(RiskBase):
    """Model for Directors & Officers risk assessment."""
    # TODO: add class-specific fields, e.g. officer_count = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Directors/Officers Risk'
        verbose_name_plural = 'Directors/Officers Risks' 