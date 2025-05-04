"""
apps/risks_credit_political/models.py

Concrete model for Credit & Political Risks.
Inherits common fields from RiskBase; adds class-specific fields.
"""
from django.db import models
from apps.risks_core.models import RiskBase


class CreditPoliticalRisk(RiskBase):
    """Model for credit & political risk assessment."""
    # Example of a class-specific field; extend with domain-specific attributes
    credit_score = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Credit/Political Risk'
        verbose_name_plural = 'Credit/Political Risks' 