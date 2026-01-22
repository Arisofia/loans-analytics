from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.abaco_pipeline.quality.gates import compute_freshness_hours


def test_compute_freshness_hours_zero_when_same_time():
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert compute_freshness_hours(as_of=now, now=now) == 0.0


def test_compute_freshness_hours_positive_delta():
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    as_of = now - timedelta(hours=6)
    assert compute_freshness_hours(as_of=as_of, now=now) == 6.0
