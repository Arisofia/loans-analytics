import copy
from typing import Any, Dict, List


class DataCleaningAgent:
    """Provide safe, side-effect free cleaning of ingested records."""

    def clean_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return cleaned copies of records without mutating the originals."""

        cleaned_records: List[Dict[str, Any]] = []
        for record in records:
            sanitized = copy.deepcopy(record)
            for key, value in sanitized.items():
                if isinstance(value, str):
                    sanitized[key] = value.strip()
            cleaned_records.append(sanitized)
        return cleaned_records
