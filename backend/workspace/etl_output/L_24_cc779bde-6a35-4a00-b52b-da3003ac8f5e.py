"""
Load — upsert transformed records into the CampaignRecord table.
"""
import logging
from typing import Any, Dict, List

from .models import CampaignRecord, ClientDataSource, ETLRun

logger = logging.getLogger(__name__)


class Loader:
    """
    Takes a list of cleaned dicts and upserts them into
    CampaignRecord for the given data-source.
    """

    def __init__(self, data_source: ClientDataSource, run: ETLRun | None = None):
        self.data_source = data_source
        self.run = run
        self.created_count: int = 0
        self.updated_count: int = 0
        self.rows_loaded: int = 0

    def load(self, records: List[Dict[str, Any]]) -> None:
        if not records:
            logger.warning("Nothing to load — empty record list.")
            return

        record_id_field = self.data_source.record_id_field or "id"

        for row in records:
            raw_id = row.get(record_id_field)
            if raw_id is None:
                continue

            kacicall_id = str(raw_id).strip()
            if not kacicall_id:
                continue

            _, created = CampaignRecord.objects.update_or_create(
                data_source=self.data_source,
                kacicall_record_id=kacicall_id,
                defaults={
                    "data": row,
                    "source_run": self.run,
                },
            )
            if created:
                self.created_count += 1
            else:
                self.updated_count += 1

        self.rows_loaded = self.created_count + self.updated_count
        logger.info(
            "Loaded %d records (created=%d, updated=%d).",
            self.rows_loaded,
            self.created_count,
            self.updated_count,
        )

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "rows_loaded": self.rows_loaded,
            "created_count": self.created_count,
            "updated_count": self.updated_count,
        }