"""Audit support for KPI formula executions."""

from __future__ import annotations

from typing import Any


class KPIFormulaAuditor:
    """In-memory audit sink used by formula engine execution paths."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record(self, entry: dict[str, Any]) -> None:
        self._records.append(dict(entry))

    def all_records(self) -> list[dict[str, Any]]:
        return list(self._records)
