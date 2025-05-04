import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

# Create your models here.

class User(AbstractUser):
    """Use Django's built-in user; extend only when needed."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Add any user-specific fields here in the future
    pass 

# MagicLink model to support click-to-login magic links
class MagicLinkQuerySet(models.QuerySet):
    def valid(self):
        """
        Return magic links that are not used and not expired.
        """
        expiry_delta = timedelta(minutes=settings.MAGIC_LINK_EXPIRY_MINUTES)
        cutoff = timezone.now() - expiry_delta
        return self.filter(used=False, created_at__gt=cutoff)

class MagicLinkManager(models.Manager):
    def get_queryset(self):
        return MagicLinkQuerySet(self.model, using=self._db)

    def valid(self):
        return self.get_queryset().valid()

class MagicLink(models.Model):
    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='magic_links')
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    objects = MagicLinkManager()  # Use custom manager to centralize valid() filtering

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f"MagicLink(token={self.token}, user={self.user.email})" 