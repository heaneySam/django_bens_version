"""
apps/risks_core/apps.py

Core app config for shared risk base classes and utilities.
"""
from django.apps import AppConfig


class RisksCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.risks_core'
    verbose_name = 'Risks Core' 