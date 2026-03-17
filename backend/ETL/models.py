from django.conf import settings
from django.db import models


class ClientDataSource(models.Model):
    """
    A LeaCall campaign linked to a BI client.
    Each client can have multiple campaigns (marketing, SAV, vente …)
    and each campaign has its own set of fields.
    """

    class CampaignType(models.TextChoices):
        MARKETING = "marketing", "Marketing"
        SAV = "sav", "SAV"
        VENTE = "vente", "Vente"
        OTHER = "other", "Autre"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,#####
        on_delete=models.CASCADE,
        related_name="data_sources",
    )
    campaign_id = models.CharField(
        max_length=128,
        help_text="Campaign ID in the LeaCall system.",
    )
    campaign_name = models.CharField(max_length=255, blank=True)
    campaign_type = models.CharField(
        max_length=16,
        choices=CampaignType.choices,
        default=CampaignType.OTHER,
    )
    # API endpoint on the LeaCall server to fetch records (e.g. /api/campaigns/{id}/contacts/)
    api_endpoint = models.CharField(
        max_length=512,
        blank=True,
        help_text="LeaCall API endpoint for this campaign's data. "
                  "Leave blank to use the default: /api/campaigns/{campaign_id}/contacts/",
    )
    # The field in LeaCall that uniquely identifies each record
    record_id_field = models.CharField(
        max_length=128,
        default="id",
        help_text="Name of the unique-ID field in LeaCall records.",
    )
    # Optional mapping: leacall_field_name → display_name
    field_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"leacall_field": "Display Name"} — empty means keep original names.',
    )
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client", "campaign_name"]
        unique_together = ("client", "campaign_id")

    def __str__(self):
        return f"{self.client} — {self.campaign_name or self.campaign_id}"

    def get_api_endpoint(self) -> str:
        if self.api_endpoint:
            return self.api_endpoint
        return f"/api/bi/campaigns/{self.campaign_id}/leads/"


# ─── ETL Run ──────────────────────────────────────────────────────────────────


class ETLRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    data_source = models.ForeignKey(
        ClientDataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="runs",
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="etl_runs",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    raw_count = models.PositiveIntegerField(default=0)
    transformed_count = models.PositiveIntegerField(default=0)
    loaded_count = models.PositiveIntegerField(default=0)
    stats = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ETLRun#{self.pk} [{self.status}]"


# ─── Raw records (stage 1) ────────────────────────────────────────────────────


class ETLRawRecord(models.Model):
    run = models.ForeignKey(ETLRun, on_delete=models.CASCADE, related_name="raw_records")
    row_index = models.PositiveIntegerField()
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["row_index"]
        unique_together = ("run", "row_index")


# ─── Campaign records (final cleaned data — dynamic schema) ──────────────────


class CampaignRecord(models.Model):
    """
    Cleaned record belonging to a specific campaign/data-source.
    Because every client has different fields, the actual values live
    in the ``data`` JSONField.
    """

    data_source = models.ForeignKey(
        ClientDataSource,
        on_delete=models.CASCADE,
        related_name="records",
    )
    source_run = models.ForeignKey(
        ETLRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_records",
    )
    leacall_record_id = models.CharField(
        max_length=255,
        help_text="Original record ID from the LeaCall system.",
    )
    data = models.JSONField(
        default=dict,
        help_text="Dynamic key/value pairs extracted from the campaign.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ("data_source", "leacall_record_id")
