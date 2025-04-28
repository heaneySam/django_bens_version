from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserListViewSet, RequestMagicLinkView, ConfirmMagicLinkView, SessionView, CSRFCookieView

# Router for the admin user list viewset
router = DefaultRouter()
router.register(r'list', UserListViewSet, basename='user-list') # Register under /api/users/list/

# URLs for the users app
urlpatterns = [
    # Admin user list
    path('users/', include(router.urls)),

    # Custom Magic Link API endpoints
    path('auth/code/request/', RequestMagicLinkView.as_view(), name='api_request_code'),
    # Endpoint for click-to-login magic link confirm
    path('auth/magic/confirm/', ConfirmMagicLinkView.as_view(), name='confirm_magic_link'),
    # Current session info
    path('auth/session/', SessionView.as_view(), name='api_session'),
    # CSRF token setter
    path('auth/csrf/', CSRFCookieView.as_view(), name='api_csrf'),
] 