"""
Transform — clean and normalise raw LeaCall records.

Because each client / campaign has different fields, transformation
is *dynamic*: we strip whitespace on strings, drop empty-ID rows,
apply an optional field_mapping, and return clean dicts.
"""
import logging
from typing import Any, Dict, List

from .models import ClientDataSource, ETLRun

logger = logging.getLogger(__name__)


class Transformer:
    """
    Receives the raw list of dicts pulled from the LeaCall API and
    returns a cleaned list ready for loading.
    """

    def __init__(
        self,
        data: List[Dict[str, Any]],
        data_source: ClientDataSource,
        run: ETLRun | None = None,
    ):
        self.data = data
        self.data_source = data_source
        self.run = run
        self.transformed: List[Dict[str, Any]] = []
        self.record_id_field: str = data_source.record_id_field or "id"
        self.field_mapping: Dict[str, str] = data_source.field_mapping or {}

    def transform(self) -> List[Dict[str, Any]]:
        if not self.data:
            logger.warning("No raw records to transform.")
            return []

        seen_ids: set = set()

        for row in self.data:
            cleaned = self._clean_row(row)

            # Every record must have a non-empty unique ID
            record_id = str(cleaned.get(self.record_id_field, "")).strip()
            if not record_id:
                continue

            # Deduplicate on the ID field
            if record_id in seen_ids:
                continue
            seen_ids.add(record_id)

            # Apply optional field renaming
            if self.field_mapping:
                cleaned = {
                    self.field_mapping.get(k, k): v
                    for k, v in cleaned.items()
                }

            self.transformed.append(cleaned)

        logger.info(
            "Transformed %d / %d records (dropped %d).",
            len(self.transformed),
            len(self.data),
            len(self.data) - len(self.transformed),
        )
        return self.transformed

    @staticmethod
    def _clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """Strip strings, convert None → ''."""
        cleaned: Dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, str):
                cleaned[key] = value.strip()
            elif value is None:
                cleaned[key] = ""
            else:
                cleaned[key] = value
        return cleaned

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "input_count": len(self.data),
            "output_count": len(self.transformed),
            "dropped_count": len(self.data) - len(self.transformed),
            "fields": list(self.transformed[0].keys()) if self.transformed else [],
        }
