from .base import *
import os

# Disable debug mode explicitly
DEBUG = False

# Allowed hosts for production
ALLOWED_HOSTS = [
    "api.riskwizard.dev",
    "djangomvp.onrender.com",
]

# CORS settings for production
# tells Django which origins can make cross-site HTTP requests.
CORS_ALLOWED_ORIGINS = [
    "https://riskwizard.dev",
    "https://www.riskwizard.dev",
]

# tells Django's own CSRF machinery when you're using CSRF_TRUSTED_ORIGINS (Django≥4.0) to allow cookies on cross-site POSTs.
CSRF_TRUSTED_ORIGINS = [
    "https://riskwizard.dev",
    "https://www.riskwizard.dev",   # your actual front-end origin
]

# Security Hardening
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_DOMAIN = ".riskwizard.dev"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN    = ".riskwizard.dev"
CSRF_COOKIE_SECURE = True