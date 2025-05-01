from .base import *
import os

# Enable debug mode
DEBUG = True

# Hosts allowed in development
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

# CORS settings for local frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
]
