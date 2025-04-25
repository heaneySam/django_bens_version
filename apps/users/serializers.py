from rest_framework import serializers
from .models import User # Make sure User model is imported

class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (read-only).
    Exposes basic, non-sensitive information.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined') # Customize fields as needed
        read_only_fields = fields # Ensure it's read-only

class RequestLoginCodeSerializer(serializers.Serializer):
    """Serializer for requesting a login code."""
    email = serializers.EmailField()

    def validate_email(self, value):
        # Optional: Add any custom validation for the email if needed
        return value

class ConfirmLoginCodeSerializer(serializers.Serializer):
    """Serializer for confirming a login code."""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=10) # Adjust max_length if needed

# Removed RequestLoginCodeSerializer

# Removed ConfirmLoginCodeSerializer 