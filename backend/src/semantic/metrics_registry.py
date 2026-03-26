"""Semantic metric registry — single source of truth for metric definitions.

Loaded from config/metrics/metric_registry.yaml and used by the KPI engine,
agents, and frontend to ensure consistent naming and computation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

_REGISTRY_PATH = Path("config/metrics/metric_registry.yaml")


class MetricDefinition:
    """In-memory representation of a single metric definition."""

    __slots__ = (
        "metric_id", "metric_name", "owner", "mart", "formula_ref",
        "unit", "description", "threshold_warning", "threshold_critical",
    )

    def __init__(self, data: Dict[str, Any]):
        self.metric_id: str = data["metric_id"]
        self.metric_name: str = data.get("metric_name", self.metric_id)
        self.owner: str = data.get("owner", "platform")
        self.mart: str = data.get("mart", "portfolio_mart")
        self.formula_ref: str = data.get("formula_ref", "")
        self.unit: str = data.get("unit", "ratio")
        self.description: str = data.get("description", "")
        self.threshold_warning: Optional[float] = data.get("threshold_warning")
        self.threshold_critical: Optional[float] = data.get("threshold_critical")


class MetricsRegistry:
    """Central registry of all metric definitions."""

    def __init__(self, definitions: Optional[List[MetricDefinition]] = None):
        self._by_id: Dict[str, MetricDefinition] = {}
        if definitions:
            for d in definitions:
                self._by_id[d.metric_id] = d

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "MetricsRegistry":
        p = path or _REGISTRY_PATH
        if not p.exists():
            logger.warning("Metric registry not found at %s, using empty registry", p)
            return cls()
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        defs = [MetricDefinition(m) for m in data.get("metrics", [])]
        logger.info("Loaded %d metric definitions from %s", len(defs), p)
        return cls(defs)

    def get(self, metric_id: str) -> Optional[MetricDefinition]:
        return self._by_id.get(metric_id)

    def list_by_owner(self, owner: str) -> List[MetricDefinition]:
        return [d for d in self._by_id.values() if d.owner == owner]

    def all_ids(self) -> List[str]:
        return list(self._by_id.keys())

    def __len__(self) -> int:
        return len(self._by_id)
