"""
apps/risks_directors_officers/urls.py

URLs for Directors & Officers Risk endpoints.
Registers the DirectorsOfficersRiskViewSet so that `/api/risks/directors-officers/` routes to it.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import DirectorsOfficersRiskViewSet

router = DefaultRouter()
router.register(r'', DirectorsOfficersRiskViewSet, basename='directors_officers_risk')

urlpatterns = [
    path('', include(router.urls)),
] 