from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiskViewSet

router = DefaultRouter()
router.register(r'risks', RiskViewSet, basename='risk')

urlpatterns = [
    path('', include(router.urls)),
] 