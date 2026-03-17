"""
Extract — pull raw records from a client's LeaCall server via REST API.
"""
import logging
from typing import Any, Dict, List

from user.leacall_client import LeacallBIClient

from .models import ETLRawRecord, ETLRun, ClientDataSource

logger = logging.getLogger(__name__)


class Extractor:
    """
    Connect to the LeaCall API for a given ClientDataSource and
    download the campaign records into raw-stage storage.
    """

    def __init__(self, data_source: ClientDataSource, run: ETLRun | None = None):
        self.data_source = data_source
        self.run = run
        self.raw_data: List[Dict[str, Any]] = []
        self._client = LeacallBIClient(data_source.client)

    def extract(self) -> List[Dict[str, Any]]:
        """
        Fetch all records from the LeaCall campaign endpoint.

        The API is expected to return either:
          • a list of dicts   →  [{"id": 1, ...}, ...]
          • a paginated dict  →  {"results": [...], "next": ...}

        Returns the flat list of record dicts.
        """
        endpoint = self.data_source.get_api_endpoint()
        logger.info("Extracting from %s%s", self._client.base_url, endpoint)

        page_url = endpoint
        while page_url:
            response = self._client.get(page_url)


            if isinstance(response, list):
                self.raw_data.extend(response)
                page_url = None
            elif isinstance(response, dict):
                self.raw_data.extend(response.get("results", []))
                page_url = response.get("next")
                # If 'next' is a full URL, convert it to a relative path
                if page_url and page_url.startswith("http"):
                    page_url = page_url.replace(self._client.base_url, "")
            else:
                break

        self._persist_raw_records()
        logger.info("Extracted %d raw records.", len(self.raw_data))
        return self.raw_data

    def _persist_raw_records(self) -> None:
        if self.run is None or not self.raw_data:
            return

        ETLRawRecord.objects.bulk_create(
            [
                ETLRawRecord(
                    run=self.run,
                    row_index=idx,
                    payload=row,
                )
                for idx, row in enumerate(self.raw_data)
            ],
            batch_size=500,
        )

    def get_info(self) -> Dict[str, Any]:
        if not self.raw_data:
            return {"source": self.data_source.get_api_endpoint(), "total_records": 0, "columns": []}
        return {
            "source": self.data_source.get_api_endpoint(),
            "total_records": len(self.raw_data),
            "columns": list(self.raw_data[0].keys()),
        }
