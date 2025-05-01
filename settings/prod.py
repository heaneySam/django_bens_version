from .base import *
import os

# Disable debug mode explicitly
DEBUG = False

# Allowed hosts for production
ALLOWED_HOSTS = [
    "api.riskwizard.dev",
]

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://riskwizard.dev",
]
CSRF_TRUSTED_ORIGINS = [
    "https://riskwizard.dev",
]

# Security Hardening
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
