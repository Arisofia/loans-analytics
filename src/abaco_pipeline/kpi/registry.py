"""KPI registry scaffold.

Keeps the mapping from KPI names to compute functions.
"""

from __future__ import annotations

from collections.abc import Callable

ComputeFn = Callable[..., object]


class KPIRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, ComputeFn] = {}

    def register(self, name: str, fn: ComputeFn) -> None:
        if not name:
            raise ValueError("KPI name is required")
        self._registry[name] = fn

    def get(self, name: str) -> ComputeFn:
        try:
            return self._registry[name]
        except KeyError as exc:
            raise KeyError(f"Unknown KPI: {name}") from exc

    def list(self) -> list[str]:
        return sorted(self._registry.keys())
