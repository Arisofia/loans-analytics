"""Validation helpers for the unified pipeline."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Dict

import pandas as pd

from python.pipeline.config import QualityGateConfig


def compute_checksum(payload: bytes) -> str:
    """Compute a deterministic checksum for payload auditing."""

    return hashlib.sha256(payload).hexdigest()


def check_freshness(as_of: datetime, max_age_hours: int) -> bool:
    """Check if the provided timestamp meets freshness requirements."""

    now = datetime.now(timezone.utc)
    delta_hours = (now - as_of).total_seconds() / 3600
    return delta_hours <= max_age_hours


def completeness_score(frame: pd.DataFrame) -> float:
    """Return the ratio of non-null cells to total cells."""

    total = frame.shape[0] * frame.shape[1]
    if total == 0:
        return 1.0
    non_null = frame.count().sum()
    return non_null / total


def enforce_quality_gates(frame: pd.DataFrame, gates: Dict[str, QualityGateConfig]) -> None:
    """Raise if quality gates are violated."""

    for name, gate in gates.items():
        if name == "completeness" and gate.threshold is not None:
            score = completeness_score(frame)
            if score < gate.threshold:
                raise ValueError(f"Completeness gate failed: {score:.2%} < {gate.threshold:.2%}")
        if name == "freshness" and gate.max_age_hours is not None:
            as_of_column = next((col for col in frame.columns if col.lower() == "as_of"), None)
            if as_of_column:
                as_of_value = pd.to_datetime(frame[as_of_column].max())
                if not check_freshness(as_of_value, gate.max_age_hours):
                    raise ValueError(
                        f"Freshness gate failed: {as_of_value.isoformat()} older than {gate.max_age_hours}h"
                    )
        if name == "referential_integrity" and gate.foreign_keys:
            missing = [col for col in gate.foreign_keys if col not in frame.columns]
            if missing:
                raise ValueError(f"Missing foreign key columns: {', '.join(missing)}")
