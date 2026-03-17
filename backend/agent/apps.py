# ==============================================================================
# agent/apps.py - Django App Configuration
# ==============================================================================
# Registers the 'agent' app with Django.
# Django uses this to discover and configure the app.
# ==============================================================================

from django.apps import AppConfig


class AgentConfig(AppConfig):
    """
    Django app configuration for the LangGraph Agent.
    This app handles ETL code generation, file management, and execution.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "agent"
    verbose_name = "LangGraph ETL Agent"
