from pathlib import Path
from uuid import uuid4
import json

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from agentKPIS.executorKPI import execute_kpi_file
from agentKPIS.models import KPIExecution
from agentKPIS.react_agent import generate_kpi_file
from ETL.models import CampaignRecord, ClientDataSource, ETLRun


def _write_fallback_kpi_file(campaign_id: str, campaign_name: str, campaign_type: str, dataset_file_path: str) -> str:
    output_dir = Path(settings.WORKSPACE_DIR) / "kpi_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_campaign_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in campaign_id)
    file_path = output_dir / f"kpi_{safe_campaign_id}_{uuid4().hex[:8]}_fallback.py"
    code = f'''import json\nfrom datetime import datetime, timezone\n\n\ndef _load_dataset():\n    with open({dataset_file_path!r}, "r", encoding="utf-8") as fp:\n        return json.load(fp)\n\n\ndef generate_kpis():\n    dataset = _load_dataset()\n    records = dataset.get("records", [])\n    latest_run = dataset.get("latest_success_run") or {{}}\n\n    return {{\n        "campaign_id": {campaign_id!r},\n        "campaign_name": {campaign_name!r},\n        "campaign_type": {campaign_type!r},\n        "generated_at": datetime.now(timezone.utc).isoformat(),\n        "status": "fallback_template",\n        "records_count": len(records),\n        "latest_loaded_count": latest_run.get("loaded_count", 0),\n        "sample_fields": sorted(list(records[0].keys())) if records else [],\n    }}\n\n\nif __name__ == "__main__":\n    print(json.dumps(generate_kpis()))\n'''
    file_path.write_text(code, encoding="utf-8")
    return str(file_path.resolve())


def _build_loaded_dataset_snapshot(client_id: int, campaign_id: str, campaign_name: str) -> tuple[str, int]:
    """
    Build a JSON snapshot from ETL-loaded records only.
    Returns (dataset_file_path, record_count).
    """
    ds = (
        ClientDataSource.objects
        .filter(client_id=client_id, campaign_id=campaign_id, is_active=True)
        .order_by("-updated_at")
        .first()
    )
    if ds is None:
        raise ValueError("Active datasource not found for this client/campaign.")

    latest_success_run = (
        ETLRun.objects
        .filter(data_source=ds, status=ETLRun.Status.SUCCESS)
        .order_by("-completed_at", "-created_at")
        .first()
    )

    records_qs = CampaignRecord.objects.filter(data_source=ds).order_by("-updated_at")
    records = [row.data for row in records_qs[:2000]]

    output_dir = Path(settings.WORKSPACE_DIR) / "kpi_output" / "datasets"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_campaign_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in campaign_id)
    dataset_file = output_dir / f"dataset_{safe_campaign_id}_{uuid4().hex[:8]}.json"

    payload = {
        "campaign_id": campaign_id,
        "campaign_name": campaign_name,
        "generated_at": timezone.now().isoformat(),
        "latest_success_run": {
            "id": latest_success_run.id,
            "status": latest_success_run.status,
            "started_at": latest_success_run.started_at.isoformat() if latest_success_run and latest_success_run.started_at else None,
            "completed_at": latest_success_run.completed_at.isoformat() if latest_success_run and latest_success_run.completed_at else None,
            "raw_count": latest_success_run.raw_count if latest_success_run else 0,
            "transformed_count": latest_success_run.transformed_count if latest_success_run else 0,
            "loaded_count": latest_success_run.loaded_count if latest_success_run else 0,
        } if latest_success_run else None,
        "records": records,
    }
    dataset_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(dataset_file.resolve()), len(records)


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

    record = KPIExecution.objects.filter(id=record_id).first() if record_id else None
    if record is None:
        record = KPIExecution.objects.create(
            ask="AUTO_INTERNAL_PROMPT",
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
        dataset_file_path, records_count = _build_loaded_dataset_snapshot(
            client_id=client_id,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
        )
        if records_count == 0:
            raise ValueError("No loaded records found. Run ETL first before generating KPI.")

        generation = generate_kpi_file(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
            dataset_file_path=dataset_file_path,
        )
        file_path = generation["file_path"]
    except Exception as exc:
        file_path = _write_fallback_kpi_file(
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

