"""Quality gate helpers used in pipeline health checks."""

from __future__ import annotations  # noqa: E402

from datetime import datetime  # noqa: E402
from typing import Optional  # noqa: E402


def compute_freshness_hours(as_of: datetime, now: Optional[datetime] = None) -> float:
    if now is None:
        now = datetime.utcnow().astimezone(as_of.tzinfo)
    delta = now - as_of
    return float(delta.total_seconds()) / 3600.0
