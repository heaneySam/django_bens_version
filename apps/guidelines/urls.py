# apps/guidelines/urls.py
from rest_framework.routers import DefaultRouter
from .views import GuidelineViewSet

router = DefaultRouter()
router.register(r'guidelines', GuidelineViewSet, basename='guideline')

urlpatterns = router.urls