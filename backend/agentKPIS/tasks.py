from pathlib import Path
import hashlib
import json
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from agentKPIS.executorKPI import execute_kpi_file
from agentKPIS.models import KPIExecution
from agentKPIS.react_agent import generate_kpi_file
from ETL.models import ClientDataSource
from ETL.tasks import build_loaded_dataset_snapshot, _safe_token, _columns_signature


logger = logging.getLogger(__name__)


def _write_fallback_kpi_file(
    user_id: int,
    campaign_id: str,
    campaign_name: str,
    campaign_type: str,
    dataset_file_path: str,
) -> str:
    """Create a deterministic fallback KPI file when LLM generation fails."""
    output_dir = Path(settings.WORKSPACE_DIR) / "kpi_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_campaign_id = _safe_token(campaign_id)
    file_path = output_dir / f"kpi_{user_id}_{safe_campaign_id}.py"
    code = f'''import json\nfrom datetime import datetime, timezone\n\n\ndef _load_dataset():\n    with open({dataset_file_path!r}, "r", encoding="utf-8") as fp:\n        return json.load(fp)\n\n\ndef generate_kpis():\n    dataset = _load_dataset()\n    records = dataset.get("records", [])\n    latest_run = dataset.get("latest_success_run") or {{}}\n\n    return {{\n        "campaign_id": {campaign_id!r},\n        "campaign_name": {campaign_name!r},\n        "campaign_type": {campaign_type!r},\n        "generated_at": datetime.now(timezone.utc).isoformat(),\n        "status": "fallback_template",\n        "records_count": len(records),\n        "latest_loaded_count": latest_run.get("loaded_count", 0),\n        "sample_fields": sorted(list(records[0].keys())) if records else [],\n    }}\n\n\nif __name__ == "__main__":\n    print(json.dumps(generate_kpis()))\n'''
    file_path.write_text(code, encoding="utf-8")
    return str(file_path.resolve())


def _cleanup_kpi_outputs(user_id: int, campaign_id: str) -> None:
    """Delete old KPI artifacts for one user/campaign before regeneration."""
    output_dir = Path(settings.WORKSPACE_DIR) / "kpi_output"
    if not output_dir.exists():
        return

    safe_campaign_id = _safe_token(campaign_id)
    patterns = [
        f"kpi_*_{safe_campaign_id}_*.py",
        f"kpi_{safe_campaign_id}_*.py",
        f"kpi_{user_id}_{safe_campaign_id}.py",
    ]
    for pattern in patterns:
        for file_path in output_dir.glob(pattern):
            if file_path.is_file():
                file_path.unlink(missing_ok=True)


def _kpi_schema_state_path(client_id: int, campaign_id: str) -> Path:
    """Return KPI-local schema state path for regenerate-vs-reuse decisions."""
    safe_campaign_id = _safe_token(campaign_id)
    output_dir = Path(settings.WORKSPACE_DIR) / "kpi_output" / "datasets"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"kpi_schema_{client_id}_{safe_campaign_id}.json"


def _read_previous_kpi_signature(client_id: int, campaign_id: str) -> str:
    """Read previous KPI schema signature; empty when missing/corrupt."""
    state_file = _kpi_schema_state_path(client_id, campaign_id)
    if not state_file.exists():
        return ""
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(payload.get("columns_signature", ""))


def _write_kpi_signature_state(client_id: int, campaign_id: str, columns: list[str], signature: str) -> None:
    """Persist KPI input schema signature to detect future KPI code invalidation."""
    state_file = _kpi_schema_state_path(client_id, campaign_id)
    payload = {
        "client_id": client_id,
        "campaign_id": campaign_id,
        "updated_at": timezone.now().isoformat(),
        "columns": sorted([str(col) for col in columns]),
        "columns_signature": signature,
    }
    state_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _kpi_file_path(user_id: int, campaign_id: str) -> Path:
    """Return deterministic KPI file path for one user/campaign pair."""
    return Path(settings.WORKSPACE_DIR) / "kpi_output" / f"kpi_{user_id}_{_safe_token(campaign_id)}.py"


@shared_task(bind=True, name="agentKPIS.generate_and_execute_kpi")
def generate_and_execute_kpi_task(self, payload: dict | None = None) -> dict:
    """
    Celery entrypoint:
    1) Ask ReAct agent to generate KPI file from internal prompt
    2) Save a DB record
    3) Execute the generated file
    4) Persist execution output + parsed KPI payload
    """

    payload = payload or {}
    record_id = payload.get("record_id")
    campaign_id = str(payload.get("campaign_id", "")).strip() or "demo_campaign"
    campaign_name = str(payload.get("campaign_name", "")).strip() or campaign_id
    campaign_type = str(payload.get("campaign_type", "general")).strip() or "general"
    client_id = payload.get("client_id")
    force_regenerate = bool(payload.get("force_regenerate", False))

    record = KPIExecution.objects.filter(id=record_id).first() if record_id else None
    if record is None:
        record = KPIExecution.objects.create(
            ask="AUTO_INTERNAL_PROMPT",
            client_id=int(client_id) if client_id not in (None, "") else None,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
            file_path="",
            celery_task_id=self.request.id or "",
            status="queued",
        )

    # KPI must be computed from ETL-loaded data only.
    try:
        if client_id in (None, ""):
            raise ValueError("Missing client_id in KPI payload.")
        client_id = int(client_id)

        data_source = (
            ClientDataSource.objects
            .filter(client_id=client_id, campaign_id=campaign_id, is_active=True)
            .order_by("-updated_at")
            .first()
        )
        if data_source is None:
            raise ValueError("Active datasource not found for this client/campaign.")

        dataset_file_path, records_count, columns = build_loaded_dataset_snapshot(
            client_id=client_id,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
        )
        if records_count == 0:
            raise ValueError("No loaded records found. Run ETL first before generating KPI.")

        # KPI task is KPI-only: schema change detection is based on KPI input dataset columns.
        current_signature = _columns_signature(columns)
        previous_signature = _read_previous_kpi_signature(client_id, campaign_id)
        has_schema_change = current_signature != previous_signature

        target_kpi_file = _kpi_file_path(client_id, campaign_id)
        # Regenerate code when forced, when schema changed, or when file is missing.
        must_regenerate = force_regenerate or has_schema_change or not target_kpi_file.exists()

        if must_regenerate:
            # Replace old KPI file with a fresh generated KPI script.
            _cleanup_kpi_outputs(client_id, campaign_id)

            generation = generate_kpi_file(
                user_id=client_id,
                campaign_id=campaign_id,
                campaign_name=campaign_name,
                campaign_type=campaign_type,
                dataset_file_path=dataset_file_path,
            )
            file_path = generation["file_path"]
        else:
            # No schema change: reuse existing generated KPI code and only execute it.
            file_path = str(target_kpi_file.resolve())

        # Persist KPI-local schema signature after this run decision.
        _write_kpi_signature_state(client_id, campaign_id, columns, current_signature)
    except Exception as exc:
        file_path = _write_fallback_kpi_file(
            user_id=int(client_id) if client_id not in (None, "") else 0,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
            dataset_file_path=dataset_file_path if "dataset_file_path" in locals() else "",
        )
        if "dataset_file_path" not in locals() or not dataset_file_path:
            record.status = "failed"
            record.error_message = f"Cannot build KPI dataset from ETL loaded data: {exc}"
            record.save(update_fields=["status", "error_message"])
            return {
                "status": "failed",
                "record_id": record.id,
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "campaign_type": campaign_type,
                "error": record.error_message,
            }

    record.ask = "AUTO_INTERNAL_PROMPT"
    record.campaign_id = campaign_id
    record.campaign_name = campaign_name
    record.campaign_type = campaign_type
    record.file_path = file_path
    if not record.celery_task_id:
        record.celery_task_id = self.request.id or ""
    record.status = "queued"
    record.save(update_fields=["ask", "campaign_id", "campaign_name", "campaign_type", "file_path", "celery_task_id", "status"])

    execution_result = execute_kpi_file(record.id)
    return {
        "status": execution_result.get("status", "failed"),
        "record_id": record.id,
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "campaign_type": campaign_type,
        "file_path": file_path,
        "celery_task_id": self.request.id,
    }


@shared_task(name="agentKPIS.refresh_all_campaign_kpis")
def refresh_all_campaign_kpis_task() -> dict:
    """
    Queue KPI refresh for every active client campaign.

    Intended to run from Celery Beat.
    """
    sources = (
        ClientDataSource.objects
        .filter(is_active=True)
        .select_related("client")
        .order_by("client_id", "campaign_name", "campaign_id")
    )

    total_sources = 0
    queued = 0
    skipped = 0
    failures = []

    for source in sources:
        total_sources += 1

        if not source.client_id:
            skipped += 1
            failures.append(
                {
                    "client_id": None,
                    "campaign_id": source.campaign_id,
                    "reason": "missing_client_id",
                }
            )
            continue

        payload = {
            "client_id": source.client_id,
            "campaign_id": source.campaign_id,
            "campaign_name": source.campaign_name or source.campaign_id,
            "campaign_type": source.campaign_type,
            "force_regenerate": False,
        }

        try:
            generate_and_execute_kpi_task.apply_async(args=[payload])
            queued += 1
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            failures.append(
                {
                    "client_id": source.client_id,
                    "campaign_id": source.campaign_id,
                    "reason": str(exc),
                }
            )

    summary = {
        "status": "completed",
        "total_sources": total_sources,
        "queued": queued,
        "skipped": skipped,
        "failures": failures,
    }
    logger.info("Beat KPI refresh summary: %s", summary)
    return summary

