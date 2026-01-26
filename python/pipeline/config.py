"""Pipeline configuration models and loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from python.models.kpi_models import KpiDefinition, KpiRegistry, KpiValidationConfig


class CascadeAuthConfig(BaseModel):
    """Authentication configuration for Cascade API access."""

    token_secret: str = Field(..., description="Environment variable name that holds the Cascade token.")
    refresh_threshold_hours: int = Field(..., ge=1, description="Hours before expiry when a refresh should occur.")


class CascadeEndpoints(BaseModel):
    """Endpoints used for Cascade API extraction."""

    risk_analytics: str
    par_rates: str
    collection_rates: str
    borrowing_base: str
    covenants: str


class CascadeConfig(BaseModel):
    """Top-level Cascade configuration."""

    base_url: str
    portfolio_id: str
    endpoints: CascadeEndpoints
    auth: CascadeAuthConfig


class QualityGateConfig(BaseModel):
    """Single data quality gate definition."""

    name: str
    threshold: Optional[float] = None
    max_age_hours: Optional[int] = None
    foreign_keys: Optional[List[str]] = None


class ValidationConfig(BaseModel):
    """Data validation configuration for pipeline outputs."""

    quality_gates: List[QualityGateConfig] = Field(default_factory=list)


class TransformationsConfig(BaseModel):
    """Transformation settings including KPI registry."""

    kpis: List[KpiDefinition]

    def registry(self) -> KpiRegistry:
        """Return a registry wrapper for KPI definitions."""

        return KpiRegistry(kpis=self.kpis)


class OutputDatabaseConfig(BaseModel):
    """Database output configuration."""

    schema: str
    tables: List[str]


class OutputsConfig(BaseModel):
    """Outputs configuration for the pipeline."""

    database: OutputDatabaseConfig


class PipelineSettings(BaseModel):
    """Base pipeline metadata."""

    name: str


class PipelineConfig(BaseModel):
    """Aggregate configuration for the unified pipeline."""

    pipeline: PipelineSettings
    cascade: CascadeConfig
    transformations: TransformationsConfig
    validation: ValidationConfig
    outputs: OutputsConfig


@dataclass(frozen=True)
class LoadedConfig:
    """Dataclass wrapper for loaded config objects."""

    model: PipelineConfig
    raw: Dict[str, Any]
    path: Path


def _resolve_portfolio(endpoint: str, portfolio_id: str) -> str:
    """Replace portfolio placeholders in configured endpoints."""

    return endpoint.replace("${portfolio_id}", portfolio_id)


def load_pipeline_config(path: Path) -> LoadedConfig:
    """Load and parse the unified pipeline configuration."""

    with path.open("r", encoding="utf-8") as handle:
        raw_config = yaml.safe_load(handle)
    model = PipelineConfig.parse_obj(raw_config)

    # Normalize endpoint placeholders once to reduce drift across modules.
    endpoints = model.cascade.endpoints
    normalized_endpoints = CascadeEndpoints(
        risk_analytics=_resolve_portfolio(endpoints.risk_analytics, model.cascade.portfolio_id),
        par_rates=_resolve_portfolio(endpoints.par_rates, model.cascade.portfolio_id),
        collection_rates=_resolve_portfolio(endpoints.collection_rates, model.cascade.portfolio_id),
        borrowing_base=_resolve_portfolio(endpoints.borrowing_base, model.cascade.portfolio_id),
        covenants=_resolve_portfolio(endpoints.covenants, model.cascade.portfolio_id),
    )
    model.cascade.endpoints = normalized_endpoints

    return LoadedConfig(model=model, raw=raw_config, path=path)
