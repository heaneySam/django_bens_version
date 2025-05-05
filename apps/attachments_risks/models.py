from django.db import models
from django.conf import settings
# Import the concrete Risk model this app relates to
from apps.risks_credit_political.models import CreditPoliticalRisk
import uuid
import os

def risk_attachment_path(instance, filename):
    """Generates the S3 path: risks/credit-political/{risk_id}/{filename_uuid}.ext"""
    # instance.risk provides access to the related CreditPoliticalRisk object
    risk_class_slug = 'credit-political' # Hardcode for this specific app
    risk_id = instance.risk.id # Use the UUID primary key from RiskBase
    # Sanitize filename & ensure uniqueness
    _, ext = os.path.splitext(filename)
    safe_filename = f"{uuid.uuid4()}{ext}" 
    return f'risks/{risk_class_slug}/{risk_id}/{safe_filename}'

class Attachment(models.Model):
    """Represents a file attached to a specific CreditPoliticalRisk."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Link to the specific Risk type
    risk = models.ForeignKey(CreditPoliticalRisk, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=risk_attachment_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    original_filename = models.CharField(max_length=255) # Store the original filename
    description = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=100, blank=True, null=True) # Store MIME type

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Risk Attachment"
        verbose_name_plural = "Risk Attachments"

    def __str__(self):
        # Use risk.id which is inherited
        return f"Attachment for Risk {self.risk.id}: {self.original_filename}"
