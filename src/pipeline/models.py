from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from src.pipeline.data_validation import DataQualityReport


class LoanRecord(BaseModel):
    """Schema enforcement for individual loan or portfolio records."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    loan_id: Optional[str] = Field(None, alias="loan_id")
    total_receivable_usd: float = Field(ge=0)
    total_eligible_usd: float = Field(ge=0)
    discounted_balance_usd: float = Field(ge=0)
    cash_available_usd: float = Field(default=0.0, ge=0)
    dpd_0_7_usd: float = Field(default=0.0, ge=0)
    dpd_7_30_usd: float = Field(default=0.0, ge=0)
    dpd_30_60_usd: float = Field(default=0.0, ge=0)
    dpd_60_90_usd: float = Field(default=0.0, ge=0)
    dpd_90_plus_usd: float = Field(default=0.0, ge=0)
    measurement_date: Optional[str] = None


@dataclass
class IngestionResult:
    """Container for ingestion outputs and metadata."""

    df: pd.DataFrame
    run_id: str
    metadata: Dict[str, Any]
    source_hash: Optional[str] = None
    raw_path: Optional[Path] = None
    quality_report: Optional[DataQualityReport] = None


@dataclass
class TransformationResult:
    """Container for transformation outputs and metadata."""

    df: pd.DataFrame
    run_id: str
    masked_columns: list[str]
    access_log: list[Dict[str, Any]]
    quality_checks: Dict[str, Any]
    lineage: list[Dict[str, Any]]
    timestamp: str


@dataclass
class CalculationResultV2:
    """Container for KPI calculation outputs and audit trail."""

    metrics: Dict[str, Any]
    audit_trail: list[Dict[str, Any]]
    run_id: str
    timeseries: Dict[str, pd.DataFrame]
    anomalies: Dict[str, Any]
    timestamp: str


@dataclass
class OutputResult:
    """Container for output persistence and manifest generation."""

    manifest: Dict[str, Any]
    manifest_path: Path
    output_paths: Dict[str, str]


@dataclass
class PersistContext:
    """Context for output persistence including quality checks and reports."""

    quality_checks: Optional[Dict[str, Any]] = None
    compliance_report_path: Optional[Path] = None
    timeseries: Optional[Dict[str, pd.DataFrame]] = None
