"""
URL configuration for djangoMVP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from api.views import health
from apps.users.views import (
    ConfirmMagicLinkView,
    RequestMagicLinkView,
    SessionView,
    CSRFCookieView,
    LogoutView,
)

urlpatterns = [
    path('', health, name='root'),
    # Magic link confirmation and code endpoints
    path('api/auth/magic/confirm/', ConfirmMagicLinkView.as_view(), name='confirm_magic_link'),
    path('api/auth/code/request/', RequestMagicLinkView.as_view(), name='api_request_code'),
    # Session and CSRF endpoints
    path('api/auth/session/', SessionView.as_view(), name='api_session'),
    path('api/auth/csrf/', CSRFCookieView.as_view(), name='api_csrf'),
    path('admin/', admin.site.urls),
    path('health/', health, name='health'),
    path('accounts/', include('allauth.urls')), # Enable allauth views including account_signup

    # Custom logout endpoint to blacklist tokens and clear cookies
    path('api/auth/logout/', LogoutView.as_view(), name='api_logout'),
    # dj-rest-auth URLs (login, logout, user, password, etc.)
    path('api/auth/', include('dj_rest_auth.urls')),
    # path('api/auth/registration/', include('dj_rest_auth.registration.urls')), # Removed: Causes ImproperlyConfigured error as socialaccount is not installed

    # API endpoints from users app (Currently only User List)
    path('api/', include('apps.users.urls')), # Includes /api/users/list/
    path('api/risks/', include('apps.risks.urls')), # Includes /api/risks/
]
