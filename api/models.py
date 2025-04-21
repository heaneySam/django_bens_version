from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.contrib.postgres.indexes import GistIndex
from django.contrib.postgres.constraints import ExclusionConstraint
from django.utils import timezone
from simple_history.models import HistoricalRecords
import uuid

# ---------------------------------------------------
# User and Enums
# ---------------------------------------------------

class User(AbstractUser):
    """Use Django's built-in user; extend only when needed."""
    pass

class InsuranceType(models.TextChoices):
    QUOTA_SHARE    = 'QUOTA_SHARE',    'Quota Share'
    EXCESS_OF_LOSS = 'EXCESS_OF_LOSS', 'Excess of Loss'
    TOP_UP         = 'TOP_UP',         'Top Up'
    FULL_COVER     = 'FULL_COVER',     'Full Cover'
    UNINSURED      = 'UNINSURED',      'Uninsured'

class InsurerStatus(models.TextChoices):
    ACTIVE    = 'ACTIVE',    'Active'
    INACTIVE  = 'INACTIVE',  'Inactive'
    SUSPENDED = 'SUSPENDED', 'Suspended'

class RiskClaimStatus(models.TextChoices):
    NONE             = 'NONE',             'None'
    WATCHLIST        = 'WATCHLIST',        'Watchlist'
    NOTIFIED         = 'NOTIFIED',         'Notified'
    UNDER_REVIEW     = 'UNDER_REVIEW',     'Under Review'
    PAID             = 'PAID',             'Paid'
    RECOVERY_PENDING = 'RECOVERY_PENDING', 'Recovery Pending'
    DENIED           = 'DENIED',           'Denied'
    CLOSED           = 'CLOSED',           'Closed'

class RiskLifecycleStage(models.TextChoices):
    SUBMITTED         = 'SUBMITTED',         'Submitted'
    UNDER_REVIEW      = 'UNDER_REVIEW',      'Under Review'
    INFO_REQUESTED    = 'INFO_REQUESTED',    'Info Requested'
    QUOTED            = 'QUOTED',            'Quoted'
    CONTRACT_DRAFTING = 'CONTRACT_DRAFTING', 'Contract Drafting'
    LIVE              = 'LIVE',              'Live'
    CANCELLED         = 'CANCELLED',         'Cancelled'
    EXPIRED           = 'EXPIRED',           'Expired'
    DECLINED          = 'DECLINED',          'Declined'
    CLOSED            = 'CLOSED',            'Closed'
    ARCHIVED          = 'ARCHIVED',          'Archived'

# ---------------------------------------------------
# Lookup Models
# ---------------------------------------------------

class CoverageType(models.Model):
    code        = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code

class Country(models.Model):
    name      = models.CharField(max_length=100)
    iso_code  = models.CharField(max_length=2, unique=True)
    region    = models.CharField(max_length=100, blank=True, default="")
    subregion = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return self.name

class CountryGrade(models.Model):
    country    = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='grades')
    grade      = models.DecimalField(max_digits=4, decimal_places=2)
    as_of_date = models.DateField()

    class Meta:
        unique_together = ('country', 'as_of_date')
        ordering = ['-as_of_date']

    def __str__(self):
        return f"{self.country.iso_code} - {self.grade} on {self.as_of_date}"

# ---------------------------------------------------
# Core Models
# ---------------------------------------------------

class Risk(models.Model):
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_risk_id      = models.UUIDField(default=uuid.uuid4, db_index=True)
    version           = models.IntegerField()
    name              = models.CharField(max_length=255, blank=True, default="")
    description       = models.TextField(blank=True, default="")
    created_at        = models.DateTimeField(default=timezone.now)
    updated_at        = models.DateTimeField(auto_now=True)
    created_by        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risks')
    lifecycle_stage   = models.CharField(max_length=50, choices=RiskLifecycleStage.choices, default=RiskLifecycleStage.SUBMITTED, db_index=True)
    is_active         = models.BooleanField(default=True)
    enquiry_data      = models.JSONField(blank=True, default=dict)
    binding_data      = models.JSONField(blank=True, default=dict)
    risk_claim_status = models.CharField(max_length=50, choices=RiskClaimStatus.choices, default=RiskClaimStatus.NONE, db_index=True)
    effective_from    = models.DateTimeField(blank=True, null=True)
    effective_to      = models.DateTimeField(blank=True, null=True)
    source            = models.CharField(max_length=50, blank=True, default="internal")

    history = HistoricalRecords()

    class Meta:
        unique_together = ('base_risk_id', 'version')
        indexes = [
            models.Index(fields=['base_risk_id', 'version'], name='risk_base_version_idx'),
            models.Index(fields=['lifecycle_stage'], name='risk_stage_idx'),
            models.Index(fields=['is_active'], name='risk_active_idx'),
        ]

class BuyerTable(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    risk        = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name='buyer_tables')
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_tables')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(default=timezone.now)
    updated_at  = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = (('risk', 'name'),)
        indexes = [
            models.Index(fields=['risk'], name='bt_risk_idx'),
            models.Index(fields=['is_active'], name='bt_active_idx'),
        ]

class Buyer(models.Model):
    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name               = models.CharField(max_length=255, blank=True, default="")
    identifier         = models.CharField(max_length=255, blank=True, default="")
    country            = models.CharField(max_length=100, blank=True, default="")
    exposure_requested = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    insurance_type     = models.CharField(max_length=50, choices=InsuranceType.choices, default=InsuranceType.QUOTA_SHARE)
    excess_amount      = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    buyer_table        = models.ForeignKey(BuyerTable, on_delete=models.CASCADE, related_name='buyers')
    is_active          = models.BooleanField(default=True)
    created_at         = models.DateTimeField(default=timezone.now)
    updated_at         = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=['buyer_table'], name='buyer_bt_idx'),
            models.Index(fields=['is_active'], name='buyer_active_idx'),
        ]

class UnderwritingEntity(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name                = models.CharField(max_length=255, blank=True, default="")
    code                = models.CharField(max_length=50, unique=True)
    is_lloyds_syndicate = models.BooleanField(default=False)
    address             = models.CharField(max_length=500, blank=True, default="")
    country             = models.CharField(max_length=100, blank=True, default="")
    financial_rating    = models.CharField(max_length=50, blank=True, default="")
    am_best_rating      = models.CharField(max_length=50, blank=True, default="")
    sp_rating           = models.CharField(max_length=50, blank=True, default="")
    moodys_rating       = models.CharField(max_length=50, blank=True, default="")
    status              = models.CharField(max_length=50, choices=InsurerStatus.choices, default=InsurerStatus.ACTIVE)
    label               = models.CharField(max_length=255, blank=True, default="")
    entity_type         = models.CharField(max_length=255, blank=True, default="")
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=['code'], name='ue_code_idx'),
            models.Index(fields=['is_lloyds_syndicate'], name='ue_lloyds_idx'),
        ]

class LloydsSyndicate(models.Model):
    underwriting_entity = models.OneToOneField(UnderwritingEntity, on_delete=models.CASCADE, primary_key=True)
    syndicate_number    = models.CharField(max_length=50, blank=True, default="")
    syndicate_year      = models.IntegerField(blank=True, null=True)
    managing_agency     = models.ForeignKey('ManagingAgency', on_delete=models.CASCADE, related_name='syndicates')
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

class ManagingAgency(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name         = models.CharField(max_length=255, blank=True, default="")
    address      = models.CharField(max_length=500, blank=True, default="")
    contact_info = models.CharField(max_length=500, blank=True, default="")
    created_at   = models.DateTimeField(default=timezone.now)
    updated_at   = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

class Coverage(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer               = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='coverages')
    underwriting_entity = models.ForeignKey(UnderwritingEntity, on_delete=models.CASCADE, related_name='coverages')
    coverage_type       = models.ForeignKey(CoverageType, on_delete=models.PROTECT, related_name='coverages')
    coverage_percent    = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    amount_covered      = models.DecimalField(max_digits=15, decimal_places=2)
    period              = DateTimeRangeField()
    is_active           = models.BooleanField(default=True)
    created_by          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coverages_created')
    created_at          = models.DateTimeField(default=timezone.now)
    updated_at          = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        indexes = [
            GistIndex(fields=['period'], name='coverage_period_gist'),
            models.Index(fields=['buyer'], name='cov_buyer_idx'),
            models.Index(fields=['underwriting_entity'], name='cov_ue_idx'),
        ]
        constraints = [
            ExclusionConstraint(
                name='no_overlap_per_buyer_entity',
                expressions=[
                    ('buyer', RangeOperators.EQUAL),
                    ('underwriting_entity', RangeOperators.EQUAL),
                    ('period', RangeOperators.OVERLAP),
                ],
                index_type='GIST'
            )
        ]
