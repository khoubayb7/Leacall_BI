import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ETL_Project.settings")

app = Celery("ETL_Project")

# Only load Django settings if Django is already configured
try:
    from django.conf import settings
    if settings.configured:
        app.config_from_object("django.conf:settings", namespace="CELERY")
        app.autodiscover_tasks()
except Exception:
    # Django not yet configured, will be handled by manage.py
    pass
