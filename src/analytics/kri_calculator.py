from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd


@dataclass
class KRIMetrics:
    """Container for the primary KRI values displayed in the dashboard."""

    portfolio_exposure: float
    delinquency_30_plus_rate: float
    delinquency_90_plus_rate: float
    average_dpd: float
    average_utilization: Optional[float]
    high_utilization_share: Optional[float]

    def as_dict(self) -> Dict[str, Optional[float]]:
        """Return KRI metrics as a dictionary."""
        return {
            "portfolio_exposure": self.portfolio_exposure,
            "delinquency_30_plus_rate": self.delinquency_30_plus_rate,
            "delinquency_90_plus_rate": self.delinquency_90_plus_rate,
            "average_dpd": self.average_dpd,
            "average_utilization": self.average_utilization,
            "high_utilization_share": self.high_utilization_share,
        }


class KRICalculator:
    """Computes Key Risk Indicators (KRIs) with graceful fallbacks."""

    @staticmethod
    def calculate(df: pd.DataFrame) -> KRIMetrics:
        """Compute the KRI metrics using available columns.

        The calculation mirrors the conditional style from the notebook example:
        Values are only produced when prerequisite columns are present;
        otherwise they default to ``np.nan``.
        """

        exposure_col = _first_present_column(df, ["outstanding_loan_value", "balance"])
        portfolio_exposure = df[exposure_col].sum(min_count=1) if exposure_col else np.nan

        if "dpd" in df.columns:
            dpd_series = df["dpd"].clip(lower=0)
            delinquency_30_plus_rate = (dpd_series >= 30).mean()
            delinquency_90_plus_rate = (dpd_series >= 90).mean()
            average_dpd = dpd_series.mean()
        else:
            delinquency_30_plus_rate = np.nan
            delinquency_90_plus_rate = np.nan
            average_dpd = np.nan

        if utilization_col := _first_present_column(df, ["utilization"]):
            utilization_series = df[utilization_col].clip(lower=0)
            average_utilization = utilization_series.mean()
            high_utilization_share = (utilization_series >= 0.8).mean()
        else:
            average_utilization = np.nan
            high_utilization_share = np.nan

        return KRIMetrics(
            portfolio_exposure=portfolio_exposure,
            delinquency_30_plus_rate=delinquency_30_plus_rate,
            delinquency_90_plus_rate=delinquency_90_plus_rate,
            average_dpd=average_dpd,
            average_utilization=average_utilization,
            high_utilization_share=high_utilization_share,
        )

    @staticmethod
    def segment_risk_mix(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Return a matrix of delinquency bucket shares per segment when available."""

        if "segment" not in df.columns or "dpd_bucket" not in df.columns:
            return None

        return (
            df.groupby(["segment", "dpd_bucket"])
            .size()
            .groupby(level=0)
            .apply(lambda s: s / s.sum())
            .unstack(fill_value=0)
            .sort_index()
        )


def _first_present_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    return next((col for col in candidates if col in df.columns), None)
