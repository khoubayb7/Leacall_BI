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

    # Always remove stale snapshot variants before writing the latest snapshot.
    _cleanup_existing_dataset_snapshots(client_id=client_id, campaign_id=campaign_id)

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


def _cleanup_existing_dataset_snapshots(client_id: int, campaign_id: str) -> None:
    """Delete stale dataset snapshot files for one client/campaign pair."""
    output_dir = Path(settings.WORKSPACE_DIR) / "etl_output" / "datasets"
    if not output_dir.exists():
        return

    safe_campaign_id = _safe_token(campaign_id)
    for file_path in output_dir.glob(f"dataset_{client_id}_{safe_campaign_id}*.json"):
        if file_path.is_file():
            file_path.unlink(missing_ok=True)


def _cleanup_existing_etl_outputs(base_dir: Path, user_id: str, campaign_id: str) -> None:
    """Delete previously generated ETL files so refresh always replaces artifacts."""
    output_patterns = [
        f"E_{user_id}_{campaign_id}*.py",
        f"T_{user_id}_{campaign_id}*.py",
        f"L_{user_id}_{campaign_id}*.py",
        f"test_E_{user_id}_{campaign_id}*.py",
        f"test_T_{user_id}_{campaign_id}*.py",
        f"test_L_{user_id}_{campaign_id}*.py",
    ]
    for pattern in output_patterns:
        for file_path in base_dir.glob(pattern):
            if file_path.is_file():
                file_path.unlink(missing_ok=True)

    # Dataset/schema artifacts live under etl_output/datasets.
    datasets_dir = base_dir / "datasets"
    if not datasets_dir.exists():
        return

    dataset_patterns = [
        f"dataset_{user_id}_{campaign_id}*.json",
        f"schema_{user_id}_{campaign_id}*.json",
    ]
    for pattern in dataset_patterns:
        for file_path in datasets_dir.glob(pattern):
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


def _queue_kpi_after_etl_success(
    *,
    data_source: ClientDataSource,
    etl_run_id: int | None,
    etl_task_id: str | None,
    force_regenerate: bool = False,
) -> dict:
    """
    Queue KPI generation for the same client/campaign after successful ETL completion.

    This function implements the ETL→KPI handoff pattern: when an ETL run completes
    successfully, automatically trigger KPI generation for the same campaign. This
    ensures KPIs are always in sync with the latest ETL data without requiring
    manual intervention.

    Args:
        data_source: The ClientDataSource that was just processed by ETL.
        etl_run_id: The ID of the completed ETLRun (for audit trail and traceability).
        etl_task_id: The Celery task ID of the ETL task (for observability).
        force_regenerate: Whether to force KPI regeneration even if cached.

    Returns:
        dict with keys:
            - queued (bool): Whether KPI task was successfully queued
            - kpi_task_id (str|None): Celery task ID of queued KPI if successful
            - error (str): Empty string on success, error message on failure
    """
    payload = {
        "client_id": data_source.client_id,
        "campaign_id": str(data_source.campaign_id),
        "campaign_name": data_source.campaign_name or data_source.campaign_id,
        "campaign_type": data_source.campaign_type,
        "force_regenerate": force_regenerate,
        "etl_run_id": etl_run_id,
        # upstream_etl_task_id allows KPI task to log and trace back to its ETL trigger
        "upstream_etl_task_id": etl_task_id,
    }

    try:
        # Import here to avoid circular dependency between ETL and agentKPIS apps
        from agentKPIS.tasks import generate_and_execute_kpi_task

        # Queue the KPI generation task asynchronously in Celery/Redis
        async_result = generate_and_execute_kpi_task.apply_async(args=[payload])
        kpi_task_id = getattr(async_result, "id", None)

        # Log the handoff for audit trail: shows ETL task→KPI task linkage
        logger.info(
            "ETL→KPI handoff queued: etl_task_id=%s etl_run_id=%s kpi_task_id=%s "
            "client_id=%s campaign_id=%s campaign_name=%s",
            etl_task_id,
            etl_run_id,
            kpi_task_id,
            data_source.client_id,
            data_source.campaign_id,
            data_source.campaign_name or data_source.campaign_id,
        )

        return {"queued": True, "kpi_task_id": kpi_task_id, "error": ""}

    except Exception as exc:
        logger.exception(
            "ETL→KPI handoff FAILED: etl_task_id=%s etl_run_id=%s client_id=%s "
            "campaign_id=%s: %s",
            etl_task_id,
            etl_run_id,
            data_source.client_id,
            data_source.campaign_id,
            exc,
        )
        return {"queued": False, "kpi_task_id": None, "error": str(exc)}


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
        else:
            # SUCCESS: ETL pipeline completed and code generation succeeded.
            # Trigger automatic KPI generation for this client/campaign so KPIs stay in sync.
            # Only queue KPI if ETL was actually successful; failures don't trigger handoff.
            _queue_kpi_after_etl_success(
                data_source=data_source,
                etl_run_id=run.id,
                etl_task_id=self.request.id,  # type: ignore[attr-defined]
                force_regenerate=False,
            )

    return run_id


@shared_task(bind=True, name="ETL.run_single_campaign_etl")
def run_single_campaign_etl_task(self, data_source_id: int) -> dict:
    """
    Celery task: Refresh ETL for a single campaign.

    This task:
    1. Fetches the active data source
    2. Executes the full ETL pipeline
    3. Updates schema signatures
    4. Regenerates E/T/L artifacts
    5. Returns a summary of the operation

    Returns a dict with operation status and details.
    """
    try:
        data_source = ClientDataSource.objects.select_related("client").filter(
            pk=data_source_id,
            is_active=True,
        ).first()

        if data_source is None:
            logger.warning(
                "run_single_campaign_etl_task: data_source %s not found or inactive",
                data_source_id,
            )
            return {
                "status": "skipped",
                "data_source_id": data_source_id,
                "reason": "datasource_not_found_or_inactive",
                "run_id": None,
                "error": "Data source not found or is inactive.",
            }

        logger.info(
            "ETL refresh START: client=%s (id=%s), campaign=%s (id=%s)",
            data_source.client.username,
            data_source.client_id,
            data_source.campaign_name or data_source.campaign_id,
            data_source.campaign_id,
        )

        # Execute the full ETL refresh pipeline
        refresh_result = refresh_campaign_etl_and_schema(data_source)

        if refresh_result.get("ok"):
            logger.info(
                "ETL refresh SUCCESS: client=%s, campaign=%s, run_id=%s, "
                "schema_change=%s, columns=%d",
                data_source.client.username,
                data_source.campaign_name or data_source.campaign_id,
                refresh_result.get("run_id"),
                refresh_result.get("has_schema_change"),
                len(refresh_result.get("columns", [])),
            )

            # SUCCESS: Nightly ETL completed successfully.
            # Trigger automatic KPI generation so KPIs update when data refreshes.
            # This ensures morning/dashboard KPI data is current with overnight data load.
            _queue_kpi_after_etl_success(
                data_source=data_source,
                etl_run_id=refresh_result.get("run_id"),
                etl_task_id=self.request.id,  # type: ignore[attr-defined]
                force_regenerate=False,
            )
        else:
            logger.error(
                "ETL refresh FAILED: client=%s, campaign=%s, run_id=%s, error=%s",
                data_source.client.username,
                data_source.campaign_name or data_source.campaign_id,
                refresh_result.get("run_id"),
                refresh_result.get("error"),
            )

        return {
            "status": "completed",
            "data_source_id": data_source_id,
            "ok": refresh_result.get("ok"),
            "run_id": refresh_result.get("run_id"),
            "error": refresh_result.get("error"),
            "has_schema_change": refresh_result.get("has_schema_change"),
        }

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "run_single_campaign_etl_task: unexpected error for data_source_id=%s: %s",
            data_source_id,
            exc,
        )
        return {
            "status": "error",
            "data_source_id": data_source_id,
            "ok": False,
            "run_id": None,
            "error": f"Unexpected error: {type(exc).__name__}: {str(exc)}",
        }


@shared_task(name="ETL.refresh_all_campaign_etls")
def refresh_all_campaign_etls_task() -> dict:
    """
    Beat schedule task: Queue ETL refresh for all active client campaigns nightly.

    This task runs on a schedule (configurable via ETL_BEAT_HOUR_UTC and
    ETL_BEAT_MINUTE_UTC environment variables, defaulting to 1:00 UTC daily).

    For each active campaign:
    - Queries only is_active=True data sources
    - Validates client exists
    - Enqueues run_single_campaign_etl_task for parallel execution
    - Logs each queued task
    - Skips and logs invalid/missing campaigns safely

    Returns a summary dict with:
        - total_sources: number of active data sources found
        - queued: number of ETL tasks successfully enqueued
        - skipped: number of campaigns that were skipped
        - failures: list of failures with reason, for audit
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

    logger.info("Beat ETL refresh STARTED: scanning active campaigns for nightly refresh")

    for source in sources:
        total_sources += 1

        # Validate that source has a valid client
        if not source.client_id:
            skipped += 1
            failure = {
                "client_id": None,
                "campaign_id": source.campaign_id,
                "campaign_name": source.campaign_name or source.campaign_id,
                "reason": "missing_client_id",
            }
            failures.append(failure)
            logger.warning(
                "Beat ETL refresh SKIP: campaign=%s has no client_id (datasource_id=%s)",
                source.campaign_id,
                source.pk,
            )
            continue

        try:
            # Enqueue the task for this campaign
            run_single_campaign_etl_task.apply_async(args=[source.pk])
            queued += 1
            logger.info(
                "Beat ETL refresh QUEUED: client=%s (id=%s), campaign=%s (id=%s, datasource_id=%s)",
                source.client.username,
                source.client_id,
                source.campaign_name or source.campaign_id,
                source.campaign_id,
                source.pk,
            )
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            failure = {
                "client_id": source.client_id,
                "campaign_id": source.campaign_id,
                "campaign_name": source.campaign_name or source.campaign_id,
                "reason": str(exc),
            }
            failures.append(failure)
            logger.error(
                "Beat ETL refresh FAILED-TO-QUEUE: client=%s, campaign=%s, error=%s",
                source.client.username,
                source.campaign_name or source.campaign_id,
                exc,
            )

    summary = {
        "status": "completed",
        "total_sources": total_sources,
        "queued": queued,
        "skipped": skipped,
        "failures": failures,
    }

    logger.info(
        "Beat ETL refresh COMPLETED: total=%d, queued=%d, skipped=%d",
        total_sources,
        queued,
        skipped,
    )

    return summary
