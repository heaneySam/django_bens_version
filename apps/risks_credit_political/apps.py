"""
apps/risks_credit_political/apps.py

Django config for the credit_political risk subclass app.
"""
from django.apps import AppConfig


class RisksCreditPoliticalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.risks_credit_political'
    verbose_name = 'Credit & Political Risks' 