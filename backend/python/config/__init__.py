from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class FinancialGuardrails(BaseModel):
    """Financial guardrails and targets for the loan portfolio."""

    min_rotation: float = Field(default=4.5)
    max_default_rate: float = Field(default=0.04)
    max_top_10_concentration: float = Field(default=0.30)
    max_single_obligor_concentration: float = Field(default=0.04)
    target_apr_min: float = Field(default=0.34)
    target_apr_max: float = Field(default=0.40)
    max_cost_of_debt: float = Field(default=0.13)
    min_dscr: float = Field(default=1.2)
    utilization_min: float = Field(default=0.75)
    utilization_max: float = Field(default=0.90)
    min_ce_6m: float = Field(default=0.96)
    max_replines_deviation: float = Field(default=0.02)


class RiskParameters(BaseModel):
    """Risk-specific business parameters."""

    dilution_threshold: float = Field(default=0.05, ge=0, le=1)
    recourse_cap: int = Field(default=100000)
    loss_given_default: float = Field(default=0.10, ge=0, le=1)


class SLASettings(BaseModel):
    """Service Level Agreements for operations."""

    decision_sla_hours: int = Field(default=24)
    funding_sla_hours: int = Field(default=48)
    sla_compliance_target: float = Field(default=0.90)
    min_slo: float = Field(default=0.995)


class AnalyticsSettings(BaseModel):
    """Settings for analytics engine and KPI calculations."""

    required_columns: list[str] = Field(
        default=[
            "loan_amount",
            "appraised_value",
            "borrower_income",
            "monthly_debt",
            "loan_status",
            "interest_rate",
            "principal_balance",
        ]
    )
    numeric_columns: list[str] = Field(
        default=[
            "loan_amount",
            "appraised_value",
            "borrower_income",
            "monthly_debt",
            "interest_rate",
            "principal_balance",
        ]
    )
    delinquent_statuses: set[str] = Field(
        default={
            "30-59 days past due",
            "60-89 days past due",
            "90+ days past due",
            "delinquent",
        }
    )
    # Ingestion specific numeric columns
    ingestion_numeric_columns: list[str] = Field(
        default=[
            "dpd_0_7_usd",
            "dpd_7_30_usd",
            "dpd_30_60_usd",
            "dpd_60_90_usd",
            "dpd_90_plus_usd",
            "total_receivable_usd",
            "total_eligible_usd",
            "discounted_balance_usd",
            "cash_available_usd",
        ]
    )
    # Data Quality Weights
    dq_null_weight: float = Field(default=1.0)
    dq_duplicate_weight: float = Field(default=0.5)
    dq_invalid_numeric_weight: float = Field(default=0.6)


class KPISettings(BaseModel):
    """Thresholds for individual KPIs."""

    portfolio_risk: dict[str, float] = Field(default={"warning": 0.03, "critical": 0.05})
    loan_book_growth: dict[str, float] = Field(default={"warning": 0.05, "critical": 0.02})
    liquidity_ratio: dict[str, float] = Field(default={"warning": 1.2, "critical": 1.0})
    compliance_breaches: dict[str, int] = Field(default={"warning": 1, "critical": 3})


class ApiSettings(BaseModel):
    """Settings for the Analytics API."""

    api_key: str = Field(
        default_factory=lambda: os.getenv("ABACO_API_KEY", ""),
        description="API key loaded from ABACO_API_KEY env var; must not be hardcoded",
    )
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)


class SupabasePoolSettings(BaseModel):
    """Supabase connection pooling configuration."""

    enabled: bool = Field(default=True, description="Enable connection pooling")
    min_size: int = Field(default=2, description="Minimum pool connections")
    max_size: int = Field(default=10, description="Maximum pool connections")
    max_idle_time: int = Field(default=300, description="Max idle time in seconds")
    max_lifetime: int = Field(default=3600, description="Max connection lifetime in seconds")
    command_timeout: int = Field(default=60, description="Command timeout in seconds")

    # Connection retry settings
    max_retries: int = Field(default=3, description="Max connection retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")


class EnvironmentSettings(BaseModel):
    """Environment configuration and data path resolution."""

    environment: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "dev"),
        description="Current environment: dev, staging, or prod",
    )
    prod_data_path: Optional[str] = Field(
        default_factory=lambda: os.getenv("PROD_DATA_PATH"),
        description="Production data mount path",
    )
    staging_data_path: Optional[str] = Field(
        default_factory=lambda: os.getenv("STAGING_DATA_PATH"),
        description="Staging data mount path",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of allowed values."""
        aliases = {"development": "dev", "production": "prod"}
        normalized = aliases.get(v.strip().lower(), v.strip().lower())
        allowed = {"dev", "staging", "prod"}
        if normalized not in allowed:
            raise ValueError(f"Environment must be one of {allowed}, got: {v}")
        return normalized

    def get_data_root(self) -> Path:
        """Get environment-specific data root path."""
        if self.environment == "prod":
            if not self.prod_data_path:
                raise RuntimeError("PROD_DATA_PATH environment variable required in production")
            return Path(self.prod_data_path)
        if self.environment == "staging":
            if not self.staging_data_path:
                raise RuntimeError("STAGING_DATA_PATH environment variable required in staging")
            return Path(self.staging_data_path)
        # Dev environment uses local data directory
        return Path("data")

    def get_test_data_root(self) -> Path:
        """Get test data path - ONLY available in dev/test environments."""
        if self.environment == "prod":
            raise RuntimeError("Test data paths are not available in production environment!")
        return Path("tests/fixtures")

    def validate_required_env_vars(self) -> None:
        """Validate production environment has required configuration."""
        if self.environment == "prod":
            required = ["PROD_DATA_PATH", "SUPABASE_URL"]
            missing = [var for var in required if not os.getenv(var)]
            has_supabase_auth = bool(
                os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )
            if not has_supabase_auth:
                missing.append("SUPABASE_ANON_KEY|SUPABASE_SERVICE_ROLE_KEY")
            if missing:
                raise RuntimeError(f"Missing required production environment variables: {missing}")


class Settings(BaseSettings):
    """Main settings class consolidating all configurations."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    runtime: EnvironmentSettings = Field(default_factory=EnvironmentSettings)
    financial: FinancialGuardrails = Field(default_factory=FinancialGuardrails)
    risk: RiskParameters = Field(default_factory=RiskParameters)
    sla: SLASettings = Field(default_factory=SLASettings)
    analytics: AnalyticsSettings = Field(default_factory=AnalyticsSettings)
    kpis: KPISettings = Field(default_factory=KPISettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    supabase_pool: SupabasePoolSettings = Field(default_factory=SupabasePoolSettings)
    portfolio_targets_2026: dict[str, int] = Field(default_factory=dict)
    database_url: Optional[str] = Field(
        default=None, description="Supabase database URL for connection pooling"
    )

    @staticmethod
    def _resolve_project_root(project_root: str | Path | None = None) -> Path:
        """Resolve repository root from the current module path unless explicitly provided."""
        if project_root is not None:
            return Path(project_root).resolve()
        return Path(__file__).resolve().parents[3]

    @classmethod
    def _candidate_config_paths(cls, project_root: str | Path | None = None) -> list[Path]:
        """Return config files ordered from base defaults to explicit overrides."""
        root = cls._resolve_project_root(project_root)
        config_dir = root / "config"
        return [
            config_dir / "business_rules.yaml",
            config_dir / "business_parameters.yml",
        ]

    @staticmethod
    def _map_guardrails_payload(yaml_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize supported guardrail schemas to FinancialGuardrails fields."""
        if "financial_guardrails" in yaml_data:
            return dict(yaml_data["financial_guardrails"] or {})

        guardrails = dict(yaml_data.get("guardrails") or {})
        if not guardrails:
            return {}

        mapped: dict[str, Any] = {}
        alias_map = {
            "target_rotation": "min_rotation",
            "max_default_rate": "max_default_rate",
            "max_top_10_concentration": "max_top_10_concentration",
            "max_single_obligor": "max_single_obligor_concentration",
            "target_apr_min": "target_apr_min",
            "target_apr_max": "target_apr_max",
            "min_dscr": "min_dscr",
            "min_collection_efficiency_6m": "min_ce_6m",
        }
        for source_key, target_key in alias_map.items():
            if source_key in guardrails:
                mapped[target_key] = guardrails[source_key]
        return mapped

    @classmethod
    def _apply_yaml_overrides(
        cls, app_settings: "Settings", yaml_data: dict[str, Any]
    ) -> "Settings":
        """Apply supported YAML overrides to the in-memory settings instance."""
        updates: dict[str, Any] = {}
        financial_payload = cls._map_guardrails_payload(yaml_data)
        if financial_payload:
            updates["financial"] = FinancialGuardrails(**financial_payload)

        if "risk_parameters" in yaml_data:
            updates["risk"] = RiskParameters(**yaml_data["risk_parameters"])
        if "sla_settings" in yaml_data:
            updates["sla"] = SLASettings(**yaml_data["sla_settings"])
        if "analytics_weights" in yaml_data:
            weights = yaml_data["analytics_weights"]
            current_analytics = app_settings.analytics.model_dump()
            current_analytics["dq_null_weight"] = weights.get(
                "dq_null_weight", current_analytics["dq_null_weight"]
            )
            current_analytics["dq_duplicate_weight"] = weights.get(
                "dq_duplicate_weight",
                current_analytics["dq_duplicate_weight"],
            )
            current_analytics["dq_invalid_numeric_weight"] = weights.get(
                "dq_invalid_numeric_weight",
                current_analytics["dq_invalid_numeric_weight"],
            )
            updates["analytics"] = AnalyticsSettings(**current_analytics)

        portfolio_targets = yaml_data.get("portfolio_targets_2026")
        if isinstance(portfolio_targets, dict):
            updates["portfolio_targets_2026"] = {
                str(month): int(str(value).replace("_", ""))
                for month, value in portfolio_targets.items()
                if len(str(month)) == 7 and str(month)[:4].isdigit() and str(month)[4] == "-"
            }

        return app_settings.model_copy(update=updates) if updates else app_settings

    @classmethod
    def load_settings(cls, project_root: str | Path | None = None) -> "Settings":
        """Load settings from environment and repository-backed YAML config."""
        app_settings = cls()

        for config_path in cls._candidate_config_paths(project_root):
            if not config_path.exists():
                continue
            with config_path.open("r", encoding="utf-8") as config_file:
                yaml_data = yaml.safe_load(config_file) or {}
            if isinstance(yaml_data, dict):
                app_settings = cls._apply_yaml_overrides(app_settings, yaml_data)

        return app_settings

    @property
    def environment(self) -> EnvironmentSettings:
        """Backwards-compatible accessor for runtime environment settings."""
        return self.runtime


# Singleton instance
settings = Settings.load_settings()
