"""
Orchestrate the full Extract → Transform → Load pipeline for a
single ClientDataSource (LeaCall campaign).
"""
import logging

from django.utils import timezone

from .extractor import Extractor
from .loader import Loader
from .models import ClientDataSource, ETLRun
from .transformer import Transformer

logger = logging.getLogger(__name__)


class ETLPipelineExecutor:

    def __init__(self, data_source: ClientDataSource):
        self.data_source = data_source

    def execute(self) -> ETLRun:
        run = ETLRun.objects.create(
            data_source=self.data_source,
            client=self.data_source.client,
            status=ETLRun.Status.RUNNING,
            started_at=timezone.now(),
        )

        try:
            # ── Extract ───────────────────────────────────────────────
            extractor = Extractor(self.data_source, run=run)
            raw_data = extractor.extract()

            # ── Transform ─────────────────────────────────────────────
            transformer = Transformer(raw_data, self.data_source, run=run)
            transformed = transformer.transform()

            # ── Load ──────────────────────────────────────────────────
            loader = Loader(self.data_source, run=run)
            loader.load(transformed)

            # ── Finalise ──────────────────────────────────────────────
            run.status = ETLRun.Status.SUCCESS
            run.raw_count = len(raw_data)
            run.transformed_count = len(transformed)
            run.loaded_count = loader.rows_loaded
            run.stats = {
                "extract": extractor.get_info(),
                "transform": transformer.get_statistics(),
                "load": loader.get_statistics(),
            }

            # Update last_synced_at on the data source
            self.data_source.last_synced_at = timezone.now()
            self.data_source.save(update_fields=["last_synced_at"])

        except Exception as exc:
            logger.exception("ETL pipeline failed for data_source=%s", self.data_source.pk)
            run.status = ETLRun.Status.FAILED
            run.error_message = str(exc)
        finally:
            run.completed_at = timezone.now()
            run.save(
                update_fields=[
                    "status",
                    "raw_count",
                    "transformed_count",
                    "loaded_count",
                    "stats",
                    "error_message",
                    "completed_at",
                ]
            )

        return run
