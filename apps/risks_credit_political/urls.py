"""
apps/risks_credit_political/urls.py

URLs for Credit & Political Risk endpoints.
Registers the CreditPoliticalRiskViewSet under the empty prefix so that `/api/risks/credit-political/` routes to it.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CreditPoliticalRiskViewSet
# Import the attachments viewset
from apps.attachments_risks.views import RiskAttachmentViewSet

router = DefaultRouter()
# Register the main risk viewset. Use a prefix like 'risks' if this isn't the root api view.
router.register(r'', CreditPoliticalRiskViewSet, basename='credit-political-risk') # Renamed basename for clarity

# urlpatterns now includes both the router's default URLs and the manual nested attachment URLs
urlpatterns = [
    path('', include(router.urls)),
    # Manual paths for nested attachments
    # Path for listing attachments for a specific risk and creating (uploading) a new one
    path('<uuid:risk_pk>/attachments/', 
         RiskAttachmentViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='risk-attachments-list-create'), # Renamed for clarity
    # Path for generating a presigned URL for a specific risk
    path('<uuid:risk_pk>/attachments/generate-upload-url/', 
         RiskAttachmentViewSet.as_view({'post': 'generate_presigned_url'}), 
         name='risk-attachments-generate-url'),
    # Path for retrieving a specific attachment for a specific risk
    path('<uuid:risk_pk>/attachments/<uuid:pk>/', 
         RiskAttachmentViewSet.as_view({'get': 'retrieve'}), # Add 'delete': 'destroy' if needed
         name='risk-attachments-detail'),
] 

# Note: The base path for this app (e.g., /api/risks/credit-political/) 
# is defined where this urls.py is included in your main project urls.py. 