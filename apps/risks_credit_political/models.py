"""
apps/risks_credit_political/models.py

Concrete model for Credit & Political Risks.
Inherits common fields from RiskBase; adds class-specific fields.
"""
from django.db import models
from apps.risks_core.models import RiskBase
from django.db.models import JSONField
from django.conf import settings


class CreditPoliticalRisk(RiskBase):
    """Model for credit & political risk assessment."""

    # Choices based on frontend table example
    PRODUCT_CHOICES = [
        ('trade_credit', 'Trade Credit'),
        ('trade_finance', 'Trade Finance'),
        ('project_finance', 'Project Finance'),
    ]
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('bound', 'Bound'),
        ('approving', 'Approving'),
        ('new_deal', 'New Deal'),
        ('approved', 'Approved'),
    ]

    # Field for unstructured data dump
    unstructured_data = JSONField(null=True, blank=True, help_text="Store unstructured third-party data before processing.")

    # Specific fields based on requirements
    insured = models.CharField(max_length=255, blank=True, default="")
    country_of_insured = models.CharField(max_length=255, blank=True, default="")
    counterparty = models.CharField(max_length=255, blank=True, default="")
    country_of_counterparty = models.CharField(max_length=255, blank=True, default="")
    product = models.CharField(max_length=50, choices=PRODUCT_CHOICES, blank=True, default="")
    country_of_risk = models.CharField(max_length=255, blank=True, default="")

    # Integration fields
    source_system = models.CharField(max_length=100, blank=True, null=True, help_text="The external system this risk originated from (e.g., Whitespace)")
    source_record_id = models.CharField(max_length=255, blank=True, null=True, unique=True, db_index=True, help_text="The unique ID of the record in the source system")

    # Use DateField for specific dates, allow nulls initially
    creation_date = models.DateField(null=True, blank=True, help_text="Business logic creation date, distinct from record creation time.")
    inception_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, blank=True, default="")
    score = models.IntegerField(null=True, blank=True, help_text="Specific risk score for this entry.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep risk even if user is deleted
        related_name='created_credit_political_risks',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Credit/Political Risk'
        verbose_name_plural = 'Credit/Political Risks' 