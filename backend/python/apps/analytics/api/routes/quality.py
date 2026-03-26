"""Data quality routes — run DQ engine, inspect rule results."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision/quality", tags=["quality"])


class QualityRunRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(
        ..., description="Loan-level records to validate."
    )


class RuleResultItem(BaseModel):
    rule_id: str
    severity: str
    passed: bool
    detail: str = ""
    blocked: bool = False


class AnomalyItem(BaseModel):
    column: str
    method: str
    outlier_count: int
    outlier_indices: List[int] = Field(default_factory=list)


class QualityRunResponse(BaseModel):
    total_rules: int
    passed: int
    failed: int
    blocked: bool
    results: List[RuleResultItem] = Field(default_factory=list)
    anomalies: List[AnomalyItem] = Field(default_factory=list)


@router.post("/run", response_model=QualityRunResponse)
async def run_quality(req: QualityRunRequest):
    """Execute the data-quality engine on the submitted records."""
    try:
        import pandas as pd

        from backend.src.data_quality.anomaly_detection import detect_anomalies
        from backend.src.data_quality.engine import run_quality_engine

        df = pd.DataFrame(req.records)
        results = run_quality_engine(df)

        items = [
            RuleResultItem(
                rule_id=getattr(r, "rule_id", "unknown"),
                severity=getattr(r, "severity", "INFO"),
                passed=getattr(r, "passed", True),
                detail=getattr(r, "detail", ""),
                blocked=getattr(r, "blocked", False),
            )
            for r in results
        ]

        blocked = any(i.blocked for i in items)
        passed_count = sum(1 for i in items if i.passed)

        # Anomaly detection on numeric columns
        anomalies: List[AnomalyItem] = []
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        for col in numeric_cols:
            try:
                outliers = detect_anomalies(df, col)
                if outliers:
                    anomalies.append(
                        AnomalyItem(
                            column=col,
                            method="zscore_iqr",
                            outlier_count=len(outliers),
                            outlier_indices=outliers[:50],  # cap for response size
                        )
                    )
            except Exception:  # noqa: BLE001
                pass

        return QualityRunResponse(
            total_rules=len(items),
            passed=passed_count,
            failed=len(items) - passed_count,
            blocked=blocked,
            results=items,
            anomalies=anomalies,
        )
    except Exception as exc:
        logger.error("Quality run error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
