"""Agent routes — inspect agent registry and individual agent status."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision/agents", tags=["agents"])

_REGISTRY_PATH = (
    Path(__file__).resolve().parents[4] / "multi_agent" / "registry" / "agents.yaml"
)


class AgentEntry(BaseModel):
    id: str
    name: str
    layer: int
    priority: int
    dependencies: List[str] = Field(default_factory=list)


class AgentListResponse(BaseModel):
    agents: List[AgentEntry]
    count: int


@router.get("/", response_model=AgentListResponse)
async def list_agents():
    """Return all registered decision agents from the YAML registry."""
    try:
        if not _REGISTRY_PATH.exists():
            return AgentListResponse(agents=[], count=0)
        with open(_REGISTRY_PATH, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        entries = [
            AgentEntry(
                id=a["id"],
                name=a.get("name", a["id"]),
                layer=a["layer"],
                priority=a.get("priority", 99),
                dependencies=a.get("dependencies", []),
            )
            for a in data.get("agents", [])
        ]
        return AgentListResponse(agents=entries, count=len(entries))
    except Exception as exc:
        logger.error("Agent list error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load agents") from exc


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Return a single agent's registry definition."""
    response = await list_agents()
    match = next((a for a in response.agents if a.id == agent_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return match
