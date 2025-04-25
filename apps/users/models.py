import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    """Use Django's built-in user; extend only when needed."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Add any user-specific fields here in the future
    pass 