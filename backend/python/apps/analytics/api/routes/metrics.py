"""Metrics engine routes — expose the unified KPI/metric engine outputs."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision/metrics", tags=["metrics-engine"])


class MetricEngineRequest(BaseModel):
    marts: Dict[str, Any] = Field(..., description="Mart DataFrames serialized as {name: records-list}")
    equity: float = Field(0.08, description="Target equity ratio")
    lgd: float = Field(0.10, description="Loss Given Default")
    min_collection_rate: float = Field(0.985, description="Minimum collection rate threshold")


class MetricEngineResponse(BaseModel):
    metrics: Dict[str, Any]
    metric_count: int


@router.post("/run", response_model=MetricEngineResponse)
async def run_metric_engine(request: MetricEngineRequest):
    """Execute the unified metric engine on pre-built mart data."""
    try:
        import pandas as pd
        from backend.src.kpi_engine.engine import run_metric_engine as _run

        marts = {k: pd.DataFrame(v) for k, v in request.marts.items()}
        result = _run(
            marts,
            equity=request.equity,
            lgd=request.lgd,
            min_collection_rate=request.min_collection_rate,
        )
        serializable = {k: float(v) if hasattr(v, "__float__") else v for k, v in result.items()}
        return MetricEngineResponse(metrics=serializable, metric_count=len(serializable))
    except Exception as exc:
        logger.error("Metric engine error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Metric engine failed") from exc
