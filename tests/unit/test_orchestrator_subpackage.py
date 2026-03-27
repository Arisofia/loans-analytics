"""Tests for the orchestrator subpackage."""

from __future__ import annotations

import pytest

from backend.python.multi_agent.orchestrator.priority_rules import (
    PRIORITY_HIERARCHY,
    AGENT_TO_CATEGORY,
    priority_rank,
    rank_actions,
    resolve_conflicts,
)
from backend.python.multi_agent.orchestrator.dependency_graph import (
    topological_sort,
)
from backend.python.multi_agent.orchestrator.action_router import (
    route_actions,
)


class TestPriorityRules:
    def test_hierarchy_ordering(self):
        assert priority_rank("data_quality") < priority_rank("sales")
        assert priority_rank("covenant") < priority_rank("pricing")

    def test_unknown_category_gets_high_rank(self):
        rank = priority_rank("nonexistent_xyz")
        assert rank >= len(PRIORITY_HIERARCHY) - 1

    def test_agent_to_category_has_entries(self):
        assert len(AGENT_TO_CATEGORY) >= 1

    def test_rank_actions_sorts_by_priority(self):
        actions = [
            {"agent_id": "sales", "action_type": "expand", "priority": 50},
            {"agent_id": "risk", "action_type": "restrict", "priority": 10},
        ]
        ranked = rank_actions(actions)
        # risk (rank 3) should come before sales/growth (rank 5)
        assert ranked[0]["agent_id"] == "risk"

    def test_resolve_conflicts_removes_expand_when_restrict_present(self):
        actions = [
            {"agent_id": "risk", "action_type": "restrict_growth", "priority": 2},
            {"agent_id": "sales", "action_type": "expand_growth", "priority": 50},
        ]
        resolved = resolve_conflicts(actions)
        action_types = [a["action_type"] for a in resolved]
        assert "expand_growth" not in action_types


class TestDependencyGraph:
    def test_topological_sort_simple(self):
        graph = {"a": [], "b": ["a"], "c": ["a", "b"]}
        order = topological_sort(graph)
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_topological_sort_no_deps(self):
        graph = {"x": [], "y": [], "z": []}
        order = topological_sort(graph)
        assert set(order) == {"x", "y", "z"}


class TestActionRouter:
    def test_route_actions_marks_routed(self):
        actions = [
            {"agent_id": "risk", "action_type": "restrict_growth", "priority": 1},
        ]
        routed = route_actions(actions)
        assert isinstance(routed, list)
        # At least the known handler should mark it routed
        for a in routed:
            if a["action_type"] == "restrict_growth":
                assert a.get("routed") is True
