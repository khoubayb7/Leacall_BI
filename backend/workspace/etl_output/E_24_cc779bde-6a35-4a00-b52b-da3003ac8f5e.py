"""
Extract — pull raw records from a client's KaciCall server via REST API.
"""
import json
import logging
from typing import Any, Dict, List

from user.kacicall_client import KaciCallBIClient

from .models import ETLRawRecord, ETLRun, ClientDataSource

logger = logging.getLogger(__name__)
TYPE_META_KEY = "__etl_types__"


class Extractor:
    """
    Connect to the KaciCall API for a given ClientDataSource and
    download the campaign records into raw-stage storage.
    """

    def __init__(self, data_source: ClientDataSource, run: ETLRun | None = None):
        self.data_source = data_source
        self.run = run
        self.raw_data: List[Dict[str, Any]] = []
        self._client = KaciCallBIClient(data_source.client)

    @staticmethod
    def _type_name(value: Any) -> str:
        if value is None:
            return "none"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int) and not isinstance(value, bool):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, dict):
            return "dict"
        if isinstance(value, list):
            return "list"
        return "str"

    @staticmethod
    def _to_string(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _stringify_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        type_map: Dict[str, str] = {}
        for key, value in row.items():
            key_str = str(key)
            payload[key_str] = self._to_string(value)
            type_map[key_str] = self._type_name(value)
        payload[TYPE_META_KEY] = type_map
        return payload

    def extract(self) -> List[Dict[str, Any]]:
        """
        Fetch all records from the KaciCall campaign endpoint.

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
                self.raw_data.extend([self._stringify_row(row) for row in response if isinstance(row, dict)])
                page_url = None
            elif isinstance(response, dict):
                results = response.get("results", [])
                self.raw_data.extend([self._stringify_row(row) for row in results if isinstance(row, dict)])
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
        columns = [k for k in self.raw_data[0].keys() if k != TYPE_META_KEY]
        return {
            "source": self.data_source.get_api_endpoint(),
            "total_records": len(self.raw_data),
            "columns": columns,
        }