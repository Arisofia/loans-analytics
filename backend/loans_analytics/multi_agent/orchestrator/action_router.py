"""Action router — dispatches ranked agent actions to downstream handlers.

Actions are routed based on type:
  - ``restrict_growth`` → block sales/marketing pipeline
  - ``liquidity_alert`` → escalate to treasury
  - ``provision_increase`` → flag for finance
  - General recommendations → surface in dashboard
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


# ── Handler registry ─────────────────────────────────────────────────────
_HANDLERS: Dict[str, Callable[[Dict[str, Any]], None]] = {}


def register_handler(action_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
    """Register a handler for a specific action type."""
    _HANDLERS[action_type] = handler


def _default_handler(action: Dict[str, Any]) -> None:
    logger.info("Action routed (no handler): %s — %s", action.get("action_type"), action.get("description"))


# ── Routing ──────────────────────────────────────────────────────────────
def route_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dispatch each action to its registered handler.

    Returns the list of actions with a ``routed`` flag added.
    """
    routed: List[Dict[str, Any]] = []
    for action in actions:
        action_type = action.get("action_type", "unknown")
        handler = _HANDLERS.get(action_type, _default_handler)
        try:
            handler(action)
            action["routed"] = True
        except Exception:
            logger.exception("Handler failed for action %s", action_type)
            action["routed"] = False
        routed.append(action)
    return routed


# ── Built-in handlers ────────────────────────────────────────────────────
def _restrict_growth_handler(action: Dict[str, Any]) -> None:
    logger.warning(
        "GROWTH RESTRICTED: %s (priority %s)",
        action.get("description", ""),
        action.get("priority", "?"),
    )


def _liquidity_alert_handler(action: Dict[str, Any]) -> None:
    logger.critical(
        "LIQUIDITY ALERT: %s (priority %s)",
        action.get("description", ""),
        action.get("priority", "?"),
    )


register_handler("restrict_growth", _restrict_growth_handler)
register_handler("liquidity_alert", _liquidity_alert_handler)
