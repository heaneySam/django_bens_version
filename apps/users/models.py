import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    """Use Django's built-in user; extend only when needed."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Add any user-specific fields here in the future
    pass 

# MagicLink model to support click-to-login magic links
class MagicLink(models.Model):
    token = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='magic_links')
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f"MagicLink(token={self.token}, user={self.user.email})" 