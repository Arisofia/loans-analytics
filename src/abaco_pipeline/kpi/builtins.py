"""Built-in KPI compute functions (v2 scaffold)."""

from __future__ import annotations


def noop_kpi(*_args: object, **_kwargs: object) -> dict[str, object]:
    return {"status": "not_implemented"}
