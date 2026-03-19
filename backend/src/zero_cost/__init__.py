"""
Zero-cost architecture adapters for Abaco Loans Analytics.

Replaces Azure services with free-tier alternatives:
  - Azure Blob / Storage Account  →  DuckDB + Parquet (local / rclone)
  - Azure SQL / Cosmos DB         →  Supabase free tier (PostgreSQL)
  - Azure Key Vault               →  GitHub Secrets / .env
  - Azure Application Insights    →  OpenTelemetry + Prometheus/Grafana
  - Azure Container Apps          →  Render / Railway / Fly.io free tiers
  - Azure Container Registry      →  GitHub Container Registry (GHCR)
"""

from .control_mora_adapter import ControlMoraAdapter
from .crosswalk import Crosswalk
from backend.python.kpis.dpd_calculator import DPDCalculator
from .exporter import Exporter
from .fuzzy_matcher import FuzzyIncomeMatcher
from .lend_id_mapper import LendIdMapper
from .local_migration_etl import (
    ETLResult,
    LocalMonthlySnapshotETL,
    build_not_specified_log,
    reconcile_payments,
)
from .loan_tape_loader import LoanTapeLoader
from .monthly_snapshot import MonthlySnapshotBuilder
from .pipeline_router import PipelineRouter
from .storage import ZeroCostStorage
from .xirr import contractual_apr, loan_xirr, portfolio_xirr, xirr

__all__ = [
    "ZeroCostStorage",
  "LendIdMapper",
    "ControlMoraAdapter",
    "MonthlySnapshotBuilder",
  "FuzzyIncomeMatcher",
    "LoanTapeLoader",
  "Crosswalk",
    "DPDCalculator",
    "PipelineRouter",
    "Exporter",
    "ETLResult",
    "LocalMonthlySnapshotETL",
    "reconcile_payments",
    "build_not_specified_log",
    "xirr",
    "contractual_apr",
    "loan_xirr",
    "portfolio_xirr",
]

