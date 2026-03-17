import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ETL_Project.settings")

app = Celery("ETL_Project")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
