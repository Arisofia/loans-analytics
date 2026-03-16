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
from .fuzzy_matcher import FuzzyIncomeMatcher
from .lend_id_mapper import LendIdMapper
from .monthly_snapshot import MonthlySnapshotBuilder
from .storage import ZeroCostStorage

__all__ = [
    "ZeroCostStorage",
    "LendIdMapper",
    "ControlMoraAdapter",
    "MonthlySnapshotBuilder",
    "FuzzyIncomeMatcher",
]
