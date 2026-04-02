from __future__ import annotations

from collections import deque

AGENT_ORDER: list[str] = [
    "data_quality",
    "risk",
    "pricing",
    "segmentation",
    "sales",
]


def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """Kahn's algorithm. graph[node] = list of dependencies (prerequisites)."""
    in_degree: dict[str, int] = {}
    reverse_adj: dict[str, list[str]] = {}
    for node in graph:
        in_degree.setdefault(node, 0)
        reverse_adj.setdefault(node, [])
        for dep in graph[node]:
            in_degree.setdefault(dep, 0)
            reverse_adj.setdefault(dep, [])
        in_degree[node] = len(graph[node])
        for dep in graph[node]:
            reverse_adj[dep].append(node)

    queue = deque(n for n, d in in_degree.items() if d == 0)
    result: list[str] = []
    while queue:
        node = queue.popleft()
        result.append(node)
        for dependent in reverse_adj.get(node, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    return result
