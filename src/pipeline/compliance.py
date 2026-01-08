import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

PII_COLUMN_KEYWORDS = [
    "name",
    "email",
    "phone",
    "address",
    "ssn",
    "tin",
    "identifier",
    "id_number",
]


def _mask_value(value: Any) -> Any:
    if pd.isnull(value):
        return value
    text = str(value)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"MASKED:{digest[:8]}"


def _redact_value(value: Any) -> Any:
    if pd.isnull(value):
        return value
    return "[REDACTED]"


def mask_pii_in_dataframe(
    df: pd.DataFrame,
    pii_columns: Optional[Iterable[str]] = None,
    keywords: Optional[Iterable[str]] = None,
    action: str = "mask",
) -> Tuple[pd.DataFrame, List[str]]:
    columns = list(pii_columns) if pii_columns is not None else []
    keyword_source = list(keywords) if keywords is not None else PII_COLUMN_KEYWORDS

    # Identify columns by keywords
    lowered_keywords = [k.lower() for k in keyword_source]
    detected_columns = [
        col
        for col in df.columns
        if any(keyword in str(col).lower() for keyword in lowered_keywords)
    ]

    # Combine detected with explicitly provided (ensuring uniqueness)
    all_pii_cols = list(set(columns + detected_columns))

    masked = df.copy()
    processed_cols = []

    for column in all_pii_cols:
        if column in masked.columns:
            if action == "redact":
                masked[column] = masked[column].apply(_redact_value)
            else:
                masked[column] = masked[column].apply(_mask_value)
            processed_cols.append(column)

    return masked, processed_cols


def create_access_log_entry(
    stage: str,
    user: str,
    action: str,
    status: str,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "stage": stage,
        "user": user,
        "action": action,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if message is not None:
        entry["message"] = message
    return entry


def build_compliance_report(
    run_id: str,
    access_log: Iterable[Dict[str, Any]],
    masked_columns: Iterable[str],
    mask_stage: str,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mask_stage": mask_stage,
        "pii_masked_columns": list(masked_columns),
        "access_log": list(access_log),
        "metadata": metadata,
    }


def write_compliance_report(report: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=str)
