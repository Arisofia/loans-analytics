"""Priority rules — conflict resolution across agent actions.

Uses the canonical priority hierarchy:
  data_integrity > regulatory_covenant > liquidity > risk > margin > growth > expansion
"""

from __future__ import annotations

from typing import Any, Dict, List


# ── Category mapping ─────────────────────────────────────────────────────
PRIORITY_HIERARCHY = [
    "data_integrity",
    "regulatory_covenant",
    "liquidity",
    "risk",
    "margin",
    "growth",
    "expansion",
]

AGENT_TO_CATEGORY: Dict[str, str] = {
    "data_quality": "data_integrity",
    "covenant": "regulatory_covenant",
    "liquidity": "liquidity",
    "risk": "risk",
    "cohort_vintage": "risk",
    "concentration": "risk",
    "collections": "risk",
    "pricing": "margin",
    "revenue_strategy": "margin",
    "cfo": "margin",
    "sales": "growth",
    "segmentation": "growth",
    "marketing": "expansion",
    "retention": "growth",
    "narrative": "expansion",
    "decision_orchestrator": "expansion",
}


def priority_rank(agent_id: str) -> int:
    """Return numeric rank (lower = higher priority) for an agent."""
    cat = AGENT_TO_CATEGORY.get(agent_id, "expansion")
    try:
        return PRIORITY_HIERARCHY.index(cat)
    except ValueError:
        return len(PRIORITY_HIERARCHY)


def rank_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort a list of action dicts by agent priority (highest first)."""
    return sorted(actions, key=lambda a: priority_rank(a.get("agent_id", "")))


def resolve_conflicts(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove lower-priority actions that contradict higher-priority ones.

    Current rule: if a ``restrict_growth`` action exists from a high-priority
    agent, drop all ``expand_growth`` actions from lower-priority agents.
    """
    restrict = any(
        a.get("action_type") == "restrict_growth"
        for a in actions
        if priority_rank(a.get("agent_id", "")) <= PRIORITY_HIERARCHY.index("risk")
    )

    if restrict:
        return [
            a for a in actions
            if a.get("action_type") != "expand_growth"
            or priority_rank(a.get("agent_id", "")) <= PRIORITY_HIERARCHY.index("risk")
        ]
    return actions
