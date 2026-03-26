"""Decision center routes — orchestrator execution and state."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision/center", tags=["decisions"])


class DecisionRunRequest(BaseModel):
    """Payload for a full orchestrator run."""
    portfolio_data: List[Dict[str, Any]] = Field(
        ..., description="Loan-level records"
    )
    business_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Override business parameters (lgd, equity, etc.)",
    )


class ActionItem(BaseModel):
    agent: str
    action: str
    priority: int = 99
    routed: bool = False


class DecisionRunResponse(BaseModel):
    business_state: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    alerts: List[str] = Field(default_factory=list)
    actions: List[ActionItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


@router.post("/run", response_model=DecisionRunResponse)
async def run_orchestrator(req: DecisionRunRequest):
    """Execute the full decision orchestrator pipeline."""
    try:
        import pandas as pd

        from backend.python.multi_agent.orchestrator import DecisionOrchestrator
        from backend.src.data_quality.engine import run_quality_engine
        from backend.src.kpi_engine.engine import run_metric_engine
        from backend.src.marts.build_all_marts import build_all_marts

        df = pd.DataFrame(req.portfolio_data)

        # Data quality gate
        dq = run_quality_engine(df)
        blocked = [r for r in dq if getattr(r, "blocked", False)]
        if blocked:
            return DecisionRunResponse(
                business_state="data_blocked",
                alerts=[f"DQ blocked: {r.rule_id}" for r in blocked],
            )

        marts = build_all_marts(df)
        rules = req.business_rules
        metrics = run_metric_engine(
            marts,
            equity=rules.get("equity", 200_000),
            lgd=rules.get("lgd", 0.10),
            min_collection_rate=rules.get("min_collection_rate", 0.985),
        )

        orch = DecisionOrchestrator()
        state = orch.run(metrics, mart_bundle=marts)

        return DecisionRunResponse(
            business_state=state.get("business_state", "unknown"),
            metrics=state.get("metrics", {}),
            alerts=state.get("alerts", []),
            actions=[
                ActionItem(**a) for a in state.get("actions", [])
            ],
            recommendations=state.get("recommendations", []),
        )
    except Exception as exc:
        logger.error("Decision run error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
