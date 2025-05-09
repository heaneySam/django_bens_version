from .base import *
import os

# Disable debug mode explicitly
DEBUG = False

# Allowed hosts for production
ALLOWED_HOSTS = [
    "api.medguides.co.uk",
    "djangomvp.onrender.com",
    "medguides-staging.onrender.com",
]

# CORS settings for production
# tells Django which origins can make cross-site HTTP requests.
CORS_ALLOWED_ORIGINS = [
    "https://medguides.co.uk",
    "https://www.medguides.co.uk",
    "https://api.medguides.co.uk",
    "https://app.medguides.co.uk",
    "https://medguides-staging.onrender.com",
]

# tells Django's own CSRF machinery when you're using CSRF_TRUSTED_ORIGINS (Django≥4.0) to allow cookies on cross-site POSTs.
CSRF_TRUSTED_ORIGINS = [
    "https://medguides.co.uk",
    "https://www.medguides.co.uk", 
    "https://app.medguides.co.uk",
    "https://medguides-staging.onrender.com",  # your actual front-end origin
]

# Security Hardening
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_DOMAIN = ".medguides.co.uk"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN    = ".medguides.co.uk"
CSRF_COOKIE_SECURE = True