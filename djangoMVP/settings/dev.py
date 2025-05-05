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

# --- Whitespace Integration Settings --- 
WHITESPACE_API_BASE_URL = os.getenv('WHITESPACE_API_BASE_URL', None)
WHITESPACE_AUTH_TOKEN = os.getenv('WHITESPACE_AUTH_TOKEN', None)
AZURE_SERVICE_BUS_CONNECTION_STRING = os.getenv('AZURE_SERVICE_BUS_CONNECTION_STRING', None)
WHITESPACE_QUEUE_NAME = os.getenv('WHITESPACE_QUEUE_NAME', None)
