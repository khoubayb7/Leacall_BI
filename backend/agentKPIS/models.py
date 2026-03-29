from django.db import models


class KPIExecution(models.Model):
    """
    Stores one KPI generation + execution run.

    We keep this model intentionally simple so interns can inspect
    what happened in each async run.
    """

    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    # Original user instruction given to the KPI agent.
    ask = models.TextField()

    # Owner account for access control and audit.
    client = models.ForeignKey(
        "user.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kpi_executions",
    )

    # Selected campaign id from client dropdown.
    campaign_id = models.CharField(max_length=255, default="demo_campaign")

    # Human-readable campaign name selected in dropdown.
    campaign_name = models.CharField(max_length=255, blank=True, default="")

    # Selected campaign type (e.g. marketing, retention, acquisition, etc.).
    campaign_type = models.CharField(max_length=255, default="general")

    # Absolute path to the generated KPI Python file.
    file_path = models.CharField(max_length=1000)

    # Celery task id to correlate API request and worker execution.
    celery_task_id = models.CharField(max_length=255, blank=True, default="")

    # Final run status after execution.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")

    # Raw stdout/stderr combined text from running the KPI file.
    execution_output = models.TextField(blank=True, default="")

    # Parsed JSON payload emitted by the generated KPI file, when valid JSON exists.
    kpi_payload = models.JSONField(blank=True, null=True)

    # Error message if generation or execution fails.
    error_message = models.TextField(blank=True, default="")

    # Creation timestamp for audit/debug.
    created_at = models.DateTimeField(auto_now_add=True)

