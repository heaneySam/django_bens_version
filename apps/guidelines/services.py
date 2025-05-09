from .models import Guideline
from django.shortcuts import get_object_or_404

class GuidelineService:
    @staticmethod
    def list_guidelines():
        """Return a queryset of all guidelines."""
        return Guideline.objects.all()

    @staticmethod
    def get_guideline(pk):
        """Return a single guideline by primary key."""
        return get_object_or_404(Guideline, pk=pk)

    @staticmethod
    def create_guideline(validated_data, user):
        """Create and return a new guideline."""
        # Set default trust_id=2 if not provided
        if 'trust' not in validated_data or validated_data['trust'] is None:
            validated_data['trust_id'] = 2
        return Guideline.objects.create(**validated_data)

    @staticmethod
    def update_guideline(guideline, validated_data):
        """Update and return the guideline instance."""
        for attr, value in validated_data.items():
            setattr(guideline, attr, value)
        guideline.save()
        return guideline

    @staticmethod
    def delete_guideline(guideline):
        """Delete the guideline instance."""
        guideline.delete()
