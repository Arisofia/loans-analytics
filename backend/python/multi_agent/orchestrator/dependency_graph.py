"""Dependency graph — topological sort for agent execution order.

Reads the agent registry to build a DAG and returns execution order
that respects dependency constraints.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_REGISTRY = (
    Path(__file__).resolve().parents[1] / "registry" / "agents.yaml"
)


def load_agent_graph(registry_path: Optional[Path] = None) -> Dict[str, List[str]]:
    """Load agents.yaml and return ``{agent_id: [dependency_ids]}``."""
    path = registry_path or _DEFAULT_REGISTRY
    if not path.exists():
        logger.warning("Agent registry not found at %s", path)
        return {}
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    graph: Dict[str, List[str]] = {}
    for entry in data.get("agents", []):
        aid = entry["id"]
        deps = entry.get("dependencies", [])
        # Wildcard "*" means depends on ALL others — resolved at sort time
        graph[aid] = [d for d in deps if d != "*"]
    return graph


def topological_sort(graph: Dict[str, List[str]]) -> List[str]:
    """Kahn's algorithm — returns agent IDs in valid execution order.

    Raises ``ValueError`` on cycles.
    """
    in_degree: Dict[str, int] = defaultdict(int)
    adjacency: Dict[str, List[str]] = defaultdict(list)

    for node in graph:
        in_degree.setdefault(node, 0)

    for node, deps in graph.items():
        for dep in deps:
            if dep in graph:
                adjacency[dep].append(node)
                in_degree[node] += 1

    queue: deque[str] = deque(n for n, d in in_degree.items() if d == 0)
    order: List[str] = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(in_degree):
        missing = set(in_degree) - set(order)
        raise ValueError(f"Cycle detected in agent dependency graph: {missing}")

    return order


def get_execution_order(registry_path: Optional[Path] = None) -> List[str]:
    """Convenience: load registry → topological sort → return ordered IDs."""
    graph = load_agent_graph(registry_path)
    return topological_sort(graph)
