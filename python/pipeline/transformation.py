"""Transformation utilities for Cascade payloads."""

from __future__ import annotations

from typing import Dict, Iterable

import pandas as pd

from python.models.cascade_schemas import CollectionResponse, RiskAnalyticsResponse


def risk_payload_to_frame(payload: RiskAnalyticsResponse) -> pd.DataFrame:
    """Convert risk analytics payload to a normalized DataFrame."""

    rows = [record.dict() for record in payload.loans]
    frame = pd.DataFrame(rows)
    frame["dpd"] = frame["dpd"].astype(int)
    frame["principal"] = frame["principal"].astype(float)
    frame["as_of"] = pd.to_datetime(payload.as_of)
    return frame


def collection_payload_to_frame(payload: CollectionResponse) -> pd.DataFrame:
    """Convert collection response to a DataFrame with enforced types."""

    rows = [record.dict() for record in payload.items]
    frame = pd.DataFrame(rows)
    for column in ("scheduled", "collected"):
        frame[column] = frame[column].astype(float)
    frame["period_start"] = pd.to_datetime(frame["period_start"])
    frame["period_end"] = pd.to_datetime(frame["period_end"])
    frame["as_of"] = pd.to_datetime(payload.as_of)
    return frame


def normalize_frames(frames: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Apply shared data hygiene steps to all frames."""

    normalized: Dict[str, pd.DataFrame] = {}
    for name, frame in frames.items():
        cleaned = frame.copy()
        cleaned = cleaned.dropna(how="all")
        cleaned.columns = [col.lower() for col in cleaned.columns]
        normalized[name] = cleaned
    return normalized
