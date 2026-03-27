"""Data quality routes — run DQ checks and retrieve results."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quality", tags=["quality"])

_LAST_QUALITY: dict | None = None


class QualityRunRequest(BaseModel):
    loans: List[Dict[str, Any]] = Field(
        ..., description="Loan records as list-of-dicts."
    )


class QualityRunResponse(BaseModel):
    quality_score: float
    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


@router.get("/current")
async def get_current_quality():
    """Return the last data quality check result."""
    if _LAST_QUALITY is None:
        return {"status": "no_run_yet"}
    return _LAST_QUALITY


@router.post("/run", response_model=QualityRunResponse)
async def run_quality(req: QualityRunRequest):
    """Execute data quality checks on a loan dataset."""
    global _LAST_QUALITY  # noqa: PLW0603
    try:
        import pandas as pd

        from backend.src.data_quality.engine import run_data_quality

        df = pd.DataFrame(req.loans)
        result = run_data_quality(df)
        _LAST_QUALITY = result
        return QualityRunResponse(**result)
    except Exception as exc:
        logger.error("Quality run error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
