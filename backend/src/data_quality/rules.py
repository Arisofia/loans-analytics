"""Data-quality rules — declarative rule definitions for mart validation.

Rules are small, composable checks that return a pass/fail + detail dict.
The DQ engine iterates over registered rules for each mart row or aggregate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKING = "blocking"


@dataclass
class RuleResult:
    """Outcome of a single rule evaluation."""

    rule_id: str
    passed: bool
    severity: Severity
    detail: Dict[str, Any] = field(default_factory=dict)
    affected_rows: int = 0


@dataclass
class Rule:
    """Declarative quality rule.

    Parameters
    ----------
    rule_id : str
        Unique identifier.
    description : str
        Human-readable explanation.
    severity : Severity
        How bad a failure is.
    check_fn : callable
        ``(pd.DataFrame) -> RuleResult``.
    mart : str | None
        Which mart this rule applies to (None = any).
    """

    rule_id: str
    description: str
    severity: Severity
    check_fn: Callable[..., RuleResult]
    mart: Optional[str] = None
    tags: List[str] = field(default_factory=list)


# ── Built-in rule catalogue ─────────────────────────────────────────────
_REGISTRY: Dict[str, Rule] = {}


def register(rule: Rule) -> Rule:
    """Add a rule to the global catalogue."""
    _REGISTRY[rule.rule_id] = rule
    return rule


def get_rule(rule_id: str) -> Optional[Rule]:
    return _REGISTRY.get(rule_id)


def list_rules(mart: Optional[str] = None) -> List[Rule]:
    if mart is None:
        return list(_REGISTRY.values())
    return [r for r in _REGISTRY.values() if r.mart is None or r.mart == mart]
