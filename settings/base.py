"""
Django Base Settings Module

This file contains the common configuration shared across all environments.

- Use `backendmvp.settings.dev` for local development (DEBUG=True, sqlite, localhost hosts).
- Use `backendmvp.settings.prod` for production (DEBUG=False, secure flags, real domains).

Set the DJANGO_SETTINGS_MODULE environment variable accordingly to switch between them.

Environment Variables & Defaults:
- SECRET_KEY: loaded from `SECRET_KEY` env var; falls back to the placeholder `ACTUALSECRETKEY`. At runtime, only one secret key is active: the env var if set, otherwise the placeholder (for dev only).
- EMAIL_HOST_PASSWORD: SMTP password from env; default is empty string in base (override in prod).
- ACCESS_TOKEN_LIFETIME / REFRESH_TOKEN_LIFETIME: parsed via `int()` from env, then passed into `timedelta` (defaults: 240 minutes / 30 days).
- FRONTEND_URL, MAGIC_LINK_EXPIRY_MINUTES: other values read from env with sensible defaults.

Override behavior:
- `dev.py` and `prod.py` import * from this base module, then redefine settings like `DEBUG`, `ALLOWED_HOSTS`, CORS/CSRF origins, and security flags to suit each environment.

Generating a real SECRET_KEY:
```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
"""

import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
# Placeholder secret key; override via environment variable in production
SECRET_KEY = os.getenv("SECRET_KEY", "EXAMPLESECRETKEY")
# DEBUG is off by default; enable in development
DEBUG = False

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework.authtoken",
    "simple_history",
    "corsheaders",

    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "dj_rest_auth",
    "rest_framework_simplejwt.token_blacklist",

    "api",
    "apps.users",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "djangoMVP.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "djangoMVP.wsgi.application"

# Database (default: SQLite)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.users.authentication.CookieJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

# Use custom User model
AUTH_USER_MODEL = "users.User"

# Sites framework
SITE_ID = 1

# Email configuration (override credentials via environment)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.resend.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "resend"
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "app@creditriskwizard.com"

# dj-rest-auth configuration
REST_AUTH = {
    "USER_DETAILS_SERIALIZER": "dj_rest_auth.serializers.UserDetailsSerializer",
    "USE_JWT": False,
}

# Simple JWT settings (override lifetimes via environment)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_LIFETIME", 240))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_LIFETIME", 30))),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
}

# Magic link expiry (minutes)
MAGIC_LINK_EXPIRY_MINUTES = int(os.getenv("MAGIC_LINK_EXPIRY_MINUTES", 5))

# Cookie settings (override in production)
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = False

# CORS defaults (override per environment)
CORS_ALLOW_CREDENTIALS = True

# Front-end base URL for magic link callback
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
