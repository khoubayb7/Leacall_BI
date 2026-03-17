# ==============================================================================
# agent/urls.py - URL Routing for the Agent App
# ==============================================================================
# Maps URL paths to view functions.
#
# KEY CONCEPTS FOR INTERNS:
#   - Each path() call maps a URL pattern to a view function
#   - The name= parameter lets you reference URLs by name in templates
#   - These URLs are prefixed with /api/ (set in etl_project/urls.py)
#
# AVAILABLE ENDPOINTS:
#   GET/POST  /api/generate/  → Custom LangGraph agent (with error loop)
#   GET/POST  /api/react/     → Prebuilt ReAct agent (simpler alternative)
#   GET       /api/health/    → Health check
# ==============================================================================

from django.urls import path
from agent import views

urlpatterns = [
    # Main endpoint: Custom graph with error-handling loop
    path("generate/", views.generate_view, name="generate"),


    # Health check
    path("health/", views.health_view, name="health"),
]
