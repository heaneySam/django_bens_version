from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    """Use Django's built-in user; extend only when needed."""
    # Add any user-specific fields here in the future
    pass 