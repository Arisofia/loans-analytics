"""KPI definition models (v2 scaffold)."""

from __future__ import annotations

from pydantic import BaseModel


class KpiValidation(BaseModel):
    min: float | None = None
    max: float | None = None


class KpiDefinition(BaseModel):
    name: str
    source_path: str
    owner: str | None = None
    precision: int | None = None
    validation: KpiValidation | None = None
