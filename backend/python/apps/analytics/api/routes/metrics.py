"""Metrics routes — compute and retrieve executive KPI metrics."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/metrics", tags=["metrics"])

_LAST_METRICS: dict | None = None


class MetricsRunRequest(BaseModel):
    marts: Dict[str, List[Dict[str, Any]]] = Field(
        ..., description="Serialised mart DataFrames as list-of-dicts."
    )


class MetricItem(BaseModel):
    metric_id: str
    metric_name: str
    value: float
    unit: str
    source_mart: str = ""
    owner: str = ""


class MetricsRunResponse(BaseModel):
    executive_metrics: List[MetricItem] = Field(default_factory=list)
    risk_metrics: List[MetricItem] = Field(default_factory=list)
    pricing_metrics: List[MetricItem] = Field(default_factory=list)


@router.get("/executive")
async def get_executive_metrics():
    """Return metrics from the last KPI engine run."""
    if _LAST_METRICS is None:
        return {"status": "no_run_yet"}
    return _LAST_METRICS


@router.post("/run", response_model=MetricsRunResponse)
async def run_metrics(req: MetricsRunRequest):
    """Compute KPIs from mart payloads and cache the result."""
    global _LAST_METRICS  # noqa: PLW0603
    try:
        import pandas as pd

        from backend.src.kpi_engine.engine import run_metric_engine

        pd_marts = {k: pd.DataFrame(v) for k, v in req.marts.items()}
        result = run_metric_engine(pd_marts)

        # Serialise MetricResult objects for JSON response
        serialised = {
            "executive_metrics": [m.model_dump() for m in result.get("executive_metrics", [])],
            "risk_metrics": [m.model_dump() for m in result.get("risk_metrics", [])],
            "pricing_metrics": [m.model_dump() for m in result.get("pricing_metrics", [])],
        }
        _LAST_METRICS = serialised
        return MetricsRunResponse(
            executive_metrics=[MetricItem(**m) for m in serialised["executive_metrics"]],
            risk_metrics=[MetricItem(**m) for m in serialised["risk_metrics"]],
            pricing_metrics=[MetricItem(**m) for m in serialised["pricing_metrics"]],
        )
    except Exception as exc:
        logger.error("Metrics run error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
