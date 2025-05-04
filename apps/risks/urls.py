"""
apps/risks/urls.py

Expose the root endpoint listing risk classes.
"""
from django.urls import include, path
from .views import RiskClassListView

urlpatterns = [
    # List available risk classes
    path('', RiskClassListView.as_view(), name='risk-class-list'),
    # Delegate to specific risk app routers
    path('credit-political/', include('apps.risks_credit_political.urls')),
    path('directors-officers/', include('apps.risks_directors_officers.urls')),
] 