from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml

class KPIRegistry:

    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self._data: dict[str, Any] | None = None
        self._index: dict[str, dict[str, Any]] | None = None

    def data(self) -> dict[str, Any]:
        if self._data is None:
            with self.registry_path.open('r', encoding='utf-8') as handle:
                self._data = yaml.safe_load(handle) or {}
        return self._data

    def version(self) -> str:
        return str(self.data().get('version', 'unknown'))

    def get(self, kpi_name: str) -> dict[str, Any]:
        if self._index is None:
            self._index = {}
            for key, section in self.data().items():
                if not key.endswith('_kpis') or not isinstance(section, dict):
                    continue
                for name, definition in section.items():
                    if isinstance(definition, dict):
                        self._index[name] = definition
        if kpi_name not in self._index:
            raise KeyError(f"KPI '{kpi_name}' not found in registry")
        return self._index[kpi_name]
