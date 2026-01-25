"""KPI definition models for the unified pipeline."""

from __future__ import annotations

from typing import Optional, Tuple

from pydantic import BaseModel, Field


class KpiValidationConfig(BaseModel):
    """Validation rules for a KPI calculation."""

    validation_range: Optional[Tuple[Optional[float], Optional[float]]] = Field(
        default=None,
        description="Inclusive min/max bounds for KPI values. Use None to disable a side of the range.",
    )
    precision: int = Field(default=2, ge=0, description="Decimal precision for rounding outputs.")


class KpiDefinition(BaseModel):
    """A single KPI definition with traceability metadata."""

    name: str = Field(..., description="Unique KPI identifier.")
    formula: str = Field(..., description="Formula expression in human-readable form.")
    source_table: str = Field(..., description="Source table or dataset used for the calculation.")
    description: Optional[str] = Field(
        default=None,
        description="Optional description to aid documentation and validation traces.",
    )
    validation: KpiValidationConfig = Field(
        default_factory=KpiValidationConfig,
        description="Validation rules applied after computation.",
    )


class KpiRegistry(BaseModel):
    """Collection of KPIs configured for a pipeline run."""

    kpis: list[KpiDefinition]

    def by_name(self, name: str) -> KpiDefinition:
        """Return the KPI matching the provided name."""

        for kpi in self.kpis:
            if kpi.name == name:
                return kpi
        raise KeyError(f"KPI '{name}' not found in registry")
