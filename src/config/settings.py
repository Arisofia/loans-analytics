from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """
    Unified application settings using Pydantic.
    This replaces static data in documentation and hardcoded thresholds.
    """

    # --- Environment ---
    env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False)

    # --- Strategic Targets 2026 ---
    aum_target_2026: float = Field(default=16.3e6, description="AUM Target for 2026 in USD")
    rotation_min: float = Field(default=4.5, description="Minimum rotation multiplier")
    npl_max: float = Field(default=0.04, description="Maximum NPL/Default rate (4%)")
    top10_concentration_max: float = Field(default=0.30, description="Maximum Top-10 concentration")
    single_obligor_max: float = Field(
        default=0.04, description="Maximum single-obligor concentration"
    )
    apr_target_min: float = Field(default=0.34, description="Minimum target weighted APR")
    apr_target_max: float = Field(default=0.40, description="Maximum target weighted APR")
    cost_of_debt_max: float = Field(default=0.13, description="Maximum cost of debt")
    dscr_min: float = Field(default=1.2, description="Minimum Debt Service Coverage Ratio")
    utilization_min: float = Field(default=0.75, description="Minimum utilization")
    utilization_max: float = Field(default=0.90, description="Maximum utilization")

    # --- SLA & Performance Targets ---
    decision_sla_hours: int = Field(default=24, description="Decision SLA in hours")
    funding_sla_hours: int = Field(default=48, description="Funding SLA in hours")
    slo_min: float = Field(default=0.995, description="Service Level Objective")
    ce_6m_min: float = Field(default=0.96, description="6-month collection efficiency minimum")

    # --- Business Logic Thresholds ---
    churn_90d_threshold_days: int = Field(default=90, description="Threshold for 90-day churn")
    churn_120d_threshold_days: int = Field(default=120, description="Threshold for 120-day churn")
    reactivation_threshold_days: int = Field(default=180, description="Threshold for reactivation")
    intensity_low_max_loans: int = Field(default=1, description="Max loans for low intensity")
    intensity_medium_max_loans: int = Field(default=3, description="Max loans for medium intensity")
    sam_penetration_market_size_usd: float = Field(
        default=0.9e9, description="SAM market size in USD"
    )

    # --- Numeric Precision ---
    outstanding_precision_threshold: float = Field(
        default=1e-4, description="Precision threshold for zero-balance"
    )

    # --- Infrastructure (Redis, Postgres, etc.) ---
    postgres_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    model_config = SettingsConfigDict(
        env_prefix="ABACO_", case_sensitive=False, env_file=".env", extra="ignore"
    )


settings = AppSettings()
