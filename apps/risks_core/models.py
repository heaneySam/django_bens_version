"""
risks_core/models.py

Abstract base model and shared QuerySet for all risk subclasses.
Improves modularity by centralizing common fields and filters.
"""
from django.db import models
import uuid
from django.conf import settings
from django.utils import timezone
from django.db.models import QuerySet


class RiskQuerySet(QuerySet):
    """Custom QuerySet for risk models: filter by owner."""
    def owned_by(self, user):
        return self.filter(created_by=user)


class RiskBase(models.Model):
    """Abstract base model for shared risk fields."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_created"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RiskQuerySet.as_manager()

    class Meta:
        abstract = True 