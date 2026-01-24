import pandas as pd
from typing import Tuple
from .validation import validate_dataframe


def _normalize_list_keys(keys, columns):
    return [k for k in (keys or []) if k in columns]


class IngestionMixin:
    """Shared logic for dataframe validation and deduplication."""

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        validation_cfg = getattr(self, "config", {}).get("validation", {})
        validate_dataframe(
            df,
            required_columns=validation_cfg.get("required_columns"),
            numeric_columns=validation_cfg.get("numeric_columns"),
            date_columns=validation_cfg.get("date_columns"),
        )

    def _apply_deduplication(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        dedup_cfg = getattr(self, "config", {}).get("deduplication", {})
        if not dedup_cfg.get("enabled", False):
            return df, 0

        keys = dedup_cfg.get("key_columns")
        if not keys:
            return df, 0

        # Only use keys that actually exist in the dataframe to avoid KeyError
        valid_keys = _normalize_list_keys(keys, df.columns)
        if not valid_keys:
            return df, 0

        before = len(df)
        deduped = df.drop_duplicates(subset=valid_keys)
        deduped_count = before - len(deduped)

        return deduped, deduped_count
