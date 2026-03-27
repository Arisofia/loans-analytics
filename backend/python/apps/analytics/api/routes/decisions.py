"""Decision routes — run the decision orchestrator and retrieve results."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/decisions", tags=["decisions"])

_LAST_RESULT: dict | None = None


class DecisionRunRequest(BaseModel):
    agent_outputs: List[Dict[str, Any]] = Field(
        ..., description="List of serialised AgentOutput dicts."
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="KPI metrics bundle."
    )


class DecisionRunResponse(BaseModel):
    ranked_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    ranked_actions: List[Dict[str, Any]] = Field(default_factory=list)
    opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    agent_statuses: Dict[str, str] = Field(default_factory=dict)


@router.get("/current")
async def get_current_decisions():
    """Return the last decision orchestrator run result."""
    if _LAST_RESULT is None:
        return {"status": "no_run_yet"}
    return _LAST_RESULT


@router.post("/run", response_model=DecisionRunResponse)
async def run_decisions(req: DecisionRunRequest):
    """Execute the decision orchestrator and return ranked output."""
    global _LAST_RESULT  # noqa: PLW0603
    try:
        from backend.src.contracts.agent_schema import AgentOutput
        from backend.python.multi_agent.orchestrator.decision_orchestrator import (
            DecisionOrchestrator,
        )

        parsed_outputs = [AgentOutput(**ao) for ao in req.agent_outputs]
        orch = DecisionOrchestrator(
            agent_outputs=parsed_outputs,
            metrics=req.metrics,
        )
        result = orch.run()
        _LAST_RESULT = result
        return DecisionRunResponse(**result)
    except Exception as exc:
        logger.error("Decision run error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
