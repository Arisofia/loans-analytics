from __future__ import annotations

import os
from typing import Dict, List, Set, Optional

import yaml
from pydantic import BaseModel, Field
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
    required_columns: List[str] = Field(
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
    numeric_columns: List[str] = Field(
        default=[
            "loan_amount",
            "appraised_value",
            "borrower_income",
            "monthly_debt",
            "interest_rate",
            "principal_balance",
        ]
    )
    delinquent_statuses: Set[str] = Field(
        default={
            "30-59 days past due",
            "60-89 days past due",
            "90+ days past due",
            "delinquent",
        }
    )
    
    # Ingestion specific numeric columns
    ingestion_numeric_columns: List[str] = Field(
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
    portfolio_risk: Dict[str, float] = Field(default={"warning": 0.03, "critical": 0.05})
    loan_book_growth: Dict[str, float] = Field(default={"warning": 0.05, "critical": 0.02})
    liquidity_ratio: Dict[str, float] = Field(default={"warning": 1.2, "critical": 1.0})
    compliance_breaches: Dict[str, int] = Field(default={"warning": 1, "critical": 3})


class Settings(BaseSettings):
    """Main settings class consolidating all configurations."""
    model_config = SettingsConfigDict(env_prefix="ABACO_", env_file=".env", extra="ignore")

    financial: FinancialGuardrails = FinancialGuardrails()
    risk: RiskParameters = RiskParameters()
    sla: SLASettings = SLASettings()
    analytics: AnalyticsSettings = AnalyticsSettings()
    kpis: KPISettings = KPISettings()

    @classmethod
    def load_settings(cls) -> "Settings":
        """Load settings from environment and optional YAML config."""
        # 1. Start with defaults/env
        settings = cls()

        # 2. Optionally override with business_parameters.yml if exists
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "business_parameters.yml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    if "financial_guardrails" in yaml_data:
                        settings.financial = FinancialGuardrails(**yaml_data["financial_guardrails"])
                    if "risk_parameters" in yaml_data:
                        settings.risk = RiskParameters(**yaml_data["risk_parameters"])
                    if "sla_settings" in yaml_data:
                        settings.sla = SLASettings(**yaml_data["sla_settings"])
                    if "analytics_weights" in yaml_data:
                        # Map YAML weights to AnalyticsSettings fields
                        weights = yaml_data["analytics_weights"]
                        settings.analytics.dq_null_weight = weights.get("dq_null_weight", settings.analytics.dq_null_weight)
                        settings.analytics.dq_duplicate_weight = weights.get("dq_duplicate_weight", settings.analytics.dq_duplicate_weight)
                        settings.analytics.dq_invalid_numeric_weight = weights.get("dq_invalid_numeric_weight", settings.analytics.dq_invalid_numeric_weight)
        
        return settings


# Singleton instance
settings = Settings.load_settings()
