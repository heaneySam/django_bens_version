from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserListViewSet, RequestLoginCodeView, ConfirmLoginCodeView

# Router for the admin user list viewset
router = DefaultRouter()
router.register(r'list', UserListViewSet, basename='user-list') # Register under /api/users/list/

# URLs for the users app
urlpatterns = [
    # Admin user list
    path('users/', include(router.urls)),

    # Custom Magic Link API endpoints
    path('auth/code/request/', RequestLoginCodeView.as_view(), name='api_request_code'),
    path('auth/code/confirm/', ConfirmLoginCodeView.as_view(), name='api_confirm_code'),
] 