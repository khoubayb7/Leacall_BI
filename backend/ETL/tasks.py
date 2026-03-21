import logging
import hashlib
import json
import traceback
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from agent.graph import build_graph

from .executor import ETLPipelineExecutor
from .models import CampaignRecord, ClientDataSource, ETLRun

logger = logging.getLogger(__name__)


def _safe_token(value: str) -> str:
    """Normalize a campaign identifier so it can be used safely in file names."""
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value)


def _columns_signature(columns: list[str]) -> str:
    """Build a stable hash from the sorted schema column names."""
    normalized = sorted([str(col) for col in columns])
    joined = "|".join(normalized)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _schema_state_path(client_id: int, campaign_id: str) -> Path:
    """Return the schema-state file path stored under workspace/etl_output/datasets."""
    safe_campaign_id = _safe_token(campaign_id)
    output_dir = Path(settings.WORKSPACE_DIR) / "etl_output" / "datasets"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"schema_{client_id}_{safe_campaign_id}.json"


def _read_previous_signature(client_id: int, campaign_id: str) -> str:
    """Read the previous schema signature for this campaign, if present."""
    state_file = _schema_state_path(client_id, campaign_id)
    if not state_file.exists():
        return ""
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return str(payload.get("columns_signature", ""))


def _write_signature_state(client_id: int, campaign_id: str, columns: list[str], signature: str) -> None:
    """Persist latest schema metadata after an ETL refresh."""
    state_file = _schema_state_path(client_id, campaign_id)
    payload = {
        "client_id": client_id,
        "campaign_id": campaign_id,
        "updated_at": timezone.now().isoformat(),
        "columns": sorted([str(col) for col in columns]),
        "columns_signature": signature,
    }
    state_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_columns_from_run(data_source: ClientDataSource, run: ETLRun) -> list[str]:
    """Get schema columns from ETL stats, with CampaignRecord fallback if missing."""
    columns = []
    if isinstance(run.stats, dict):
        columns = run.stats.get("extract", {}).get("columns") or []

    if not columns:
        sample = CampaignRecord.objects.filter(data_source=data_source).order_by("-updated_at").first()
        if sample and isinstance(sample.data, dict):
            columns = sorted(sample.data.keys())

    return [str(col) for col in columns]


def build_loaded_dataset_snapshot(client_id: int, campaign_id: str, campaign_name: str) -> tuple[str, int, list[str]]:
    """
    Build a JSON snapshot from ETL-loaded records only.
    Returns (dataset_file_path, record_count, columns).
    """
    data_source = (
        ClientDataSource.objects
        .filter(client_id=client_id, campaign_id=campaign_id, is_active=True)
        .order_by("-updated_at")
        .first()
    )
    if data_source is None:
        raise ValueError("Active datasource not found for this client/campaign.")

    latest_success_run = (
        ETLRun.objects
        .filter(data_source=data_source, status=ETLRun.Status.SUCCESS)
        .order_by("-completed_at", "-created_at")
        .first()
    )

    records_qs = CampaignRecord.objects.filter(data_source=data_source).order_by("-updated_at")
    records = [row.data for row in records_qs[:2000]]

    output_dir = Path(settings.WORKSPACE_DIR) / "etl_output" / "datasets"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_campaign_id = _safe_token(campaign_id)
    dataset_file = output_dir / f"dataset_{client_id}_{safe_campaign_id}.json"

    if latest_success_run and isinstance(latest_success_run.stats, dict):
        columns = latest_success_run.stats.get("extract", {}).get("columns") or []
    else:
        columns = []
    if not columns and records:
        columns = sorted({key for row in records for key in row.keys()})

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
        "columns": columns,
    }
    dataset_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(dataset_file.resolve()), len(records), columns


def _cleanup_existing_etl_outputs(base_dir: Path, user_id: str, campaign_id: str) -> None:
    """Delete previously generated ETL files so refresh always replaces artifacts."""
    patterns = [
        f"E_{user_id}_{campaign_id}*.py",
        f"T_{user_id}_{campaign_id}*.py",
        f"L_{user_id}_{campaign_id}*.py",
        f"test_E_{user_id}_{campaign_id}*.py",
        f"test_T_{user_id}_{campaign_id}*.py",
        f"test_L_{user_id}_{campaign_id}*.py",
    ]
    for pattern in patterns:
        for file_path in base_dir.glob(pattern):
            if file_path.is_file():
                file_path.unlink(missing_ok=True)


def _generate_etl_files_for_source(data_source: ClientDataSource) -> tuple[bool, str]:
    """Generate E/T/L files for a datasource under workspace/etl_output."""
    try:
        user_id = str(data_source.client_id)
        campaign_id = _safe_token(str(data_source.campaign_id))
        output_dir = Path(settings.WORKSPACE_DIR) / "etl_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Replace mode: remove previous artifacts before writing fresh code.
        _cleanup_existing_etl_outputs(output_dir, user_id=user_id, campaign_id=campaign_id)

        mapping = data_source.field_mapping or {}
        fields = list(mapping.keys()) if mapping else [data_source.record_id_field or "id"]

        initial_state = {
            "messages": [],
            "task": (
                f"Generate an ETL pipeline for client '{data_source.client.username}', "
                f"campaign '{data_source.campaign_name or data_source.campaign_id}'. "
                f"Fields: {', '.join(fields)}."
            ),
            "new_fields": fields,
            "extract_ref_path": settings.ETL_EXTRACT_REF,
            "transform_ref_path": settings.ETL_TRANSFORM_REF,
            "load_ref_path": settings.ETL_LOAD_REF,
            "user_id": user_id,
            "campaign_id": campaign_id,
            "output_dir": str(output_dir),
            "step_order": ["E", "T", "L"],
            "current_step_index": 0,
            "current_step": "",
            "reference_file_path": "",
            "reference_code": "",
            "output_file_path": "",
            "pytest_file_path": "",
            "generated_code": "",
            "generated_test_code": "",
            "validation_ok": False,
            "test_exit_code": -1,
            "execution_result": "",
            "step_results": {},
            "error_count": 0,
            "max_retries": settings.MAX_RETRIES,
            "status": "preparing",
        }

        graph = build_graph()
        final_state = graph.invoke(initial_state)
        if final_state.get("status") == "done":
            return True, ""

        return False, f"ETL code generation ended with status={final_state.get('status')}"
    except Exception as exc:
        return False, f"ETL code generation failed: {type(exc).__name__}: {exc}\n{traceback.format_exc()}"


def refresh_campaign_etl_and_schema(data_source: ClientDataSource) -> dict:
    """
    Execute ETL refresh and update schema signature state.

    Returns:
        {
            ok: bool,
            run_id: int,
            status: str,
            columns: list[str],
            has_schema_change: bool,
            current_signature: str,
            previous_signature: str,
            error: str,
        }
    """
    # Keep dashboards fresh by always running a new ETL execution.
    run = ETLPipelineExecutor(data_source).execute()
    if run.status != ETLRun.Status.SUCCESS:
        return {
            "ok": False,
            "run_id": run.id,
            "status": run.status,
            "columns": [],
            "has_schema_change": False,
            "current_signature": "",
            "previous_signature": "",
            "error": run.error_message or "ETL refresh failed",
        }

    columns = _extract_columns_from_run(data_source, run)
    current_signature = _columns_signature(columns)
    previous_signature = _read_previous_signature(data_source.client_id, str(data_source.campaign_id))
    has_schema_change = current_signature != previous_signature

    # Persist latest signature so next refresh can decide regenerate vs reuse.
    _write_signature_state(
        client_id=data_source.client_id,
        campaign_id=str(data_source.campaign_id),
        columns=columns,
        signature=current_signature,
    )

    # On each ETL refresh, replace and regenerate E/T/L artifacts.
    codegen_ok, codegen_error = _generate_etl_files_for_source(data_source)
    if not codegen_ok:
        run.status = ETLRun.Status.FAILED
        run.error_message = codegen_error
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "error_message", "completed_at"])
        return {
            "ok": False,
            "run_id": run.id,
            "status": run.status,
            "columns": columns,
            "has_schema_change": has_schema_change,
            "current_signature": current_signature,
            "previous_signature": previous_signature,
            "error": codegen_error,
        }

    return {
        "ok": True,
        "run_id": run.id,
        "status": run.status,
        "columns": columns,
        "has_schema_change": has_schema_change,
        "current_signature": current_signature,
        "previous_signature": previous_signature,
        "error": "",
    }


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def run_etl_pipeline(self, data_source_id: int, run_id: int) -> int:
    """Run ETL in the background and return the ETLRun id."""
    try:
        run = ETLRun.objects.select_related("data_source", "client").get(pk=run_id)
    except ETLRun.DoesNotExist:
        logger.error("run_etl_pipeline: run %s not found", run_id)
        return run_id

    if run.data_source_id != data_source_id:
        logger.warning(
            "run_etl_pipeline: data_source mismatch for run=%s (expected=%s got=%s)",
            run_id,
            run.data_source_id,
            data_source_id,
        )

    data_source = run.data_source
    if data_source is None:
        data_source = ClientDataSource.objects.filter(pk=data_source_id, is_active=True).first()

    if data_source is None:
        run.status = ETLRun.Status.FAILED
        run.error_message = "Data source not found or inactive."
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "error_message", "completed_at"])
        return run_id

    executor = ETLPipelineExecutor(data_source=data_source)
    run = executor.execute(run=run)

    # Keep generated ETL artifacts in sync with each successful ETL refresh.
    if run.status == ETLRun.Status.SUCCESS:
        codegen_ok, codegen_error = _generate_etl_files_for_source(data_source)
        if not codegen_ok:
            run.status = ETLRun.Status.FAILED
            run.error_message = codegen_error
            run.completed_at = timezone.now()
            run.save(update_fields=["status", "error_message", "completed_at"])

    return run_id
