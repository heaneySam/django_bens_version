"""
apps/risks_credit_political/urls.py

URLs for Credit & Political Risk endpoints.
Registers the CreditPoliticalRiskViewSet under the empty prefix so that `/api/risks/credit-political/` routes to it.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CreditPoliticalRiskViewSet

router = DefaultRouter()
router.register(r'', CreditPoliticalRiskViewSet, basename='credit_political_risk')

urlpatterns = [
    path('', include(router.urls)),
] 