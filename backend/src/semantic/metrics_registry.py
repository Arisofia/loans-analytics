from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_metric_registry(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@dataclass
class MetricDefinition:
    metric_id: str
    metric_name: str
    unit: str = "ratio"
    mart: str = "unknown"
    owner: str = "platform"
    description: str = ""


class MetricsRegistry:
    """In-memory registry of metric definitions."""

    def __init__(self, definitions: Dict[str, MetricDefinition] | None = None):
        self._definitions: Dict[str, MetricDefinition] = definitions or {}

    @classmethod
    def load(cls, path: str | Path | None = None) -> "MetricsRegistry":
        if path is None:
            return cls()
        raw = load_metric_registry(path)
        defs: Dict[str, MetricDefinition] = {}
        for key, val in (raw or {}).items():
            if isinstance(val, dict):
                defs[key] = MetricDefinition(
                    metric_id=key,
                    metric_name=val.get("name", key),
                    unit=val.get("unit", "ratio"),
                    mart=val.get("mart", "unknown"),
                    owner=val.get("owner", "platform"),
                    description=val.get("description", ""),
                )
        return cls(defs)

    def get(self, metric_id: str) -> Optional[MetricDefinition]:
        return self._definitions.get(metric_id)

    def list_metrics(self) -> list[str]:
        return list(self._definitions.keys())
