import logging

from celery import shared_task
from django.utils import timezone

from .executor import ETLPipelineExecutor
from .models import ClientDataSource, ETLRun

logger = logging.getLogger(__name__)


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
    executor.execute(run=run)
    return run_id
