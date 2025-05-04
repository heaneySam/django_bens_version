"""
apps/risks/views.py

Aggregator API to list available risk classes for front-end selection.
All old RiskViewSet logic has moved into subclass apps for better modularity.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.risks_core.services import get_registered_risk_types


class RiskClassListView(APIView):
    """Returns the list of URL segments representing risk classes."""
    def get(self, request):
        types = get_registered_risk_types()
        return Response({"risk_classes": types})
