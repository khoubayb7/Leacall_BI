from pathlib import Path
from uuid import uuid4

from celery import shared_task
from django.conf import settings

from agentKPIS.executorKPI import execute_kpi_file
from agentKPIS.models import KPIExecution
from agentKPIS.react_agent import generate_kpi_file


def _write_fallback_kpi_file(campaign_id: str, campaign_name: str, campaign_type: str) -> str:
    output_dir = Path(settings.WORKSPACE_DIR) / "kpi_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_campaign_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in campaign_id)
    file_path = output_dir / f"kpi_{safe_campaign_id}_{uuid4().hex[:8]}_fallback.py"
    code = f'''import json\nfrom datetime import datetime, timezone\n\n\ndef generate_kpis():\n    return {{\n        "campaign_id": {campaign_id!r},\n        "campaign_name": {campaign_name!r},\n        "campaign_type": {campaign_type!r},\n        "generated_at": datetime.now(timezone.utc).isoformat(),\n        "status": "fallback_template",\n    }}\n\n\nif __name__ == "__main__":\n    print(json.dumps(generate_kpis()))\n'''
    file_path.write_text(code, encoding="utf-8")
    return str(file_path.resolve())


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

    try:
        generation = generate_kpi_file(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
        )
        file_path = generation["file_path"]
    except Exception:
        file_path = _write_fallback_kpi_file(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
        )

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

