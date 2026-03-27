"""Anomaly detection — statistical outlier and drift detection on mart data.

Uses simple Z-score and IQR methods; no heavy ML dependencies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class AnomalyReport:
    """Report for a single column/metric anomaly scan."""

    column: str
    method: str
    outlier_count: int
    total_count: int
    outlier_pct: float
    details: Dict[str, Any] = field(default_factory=dict)


def detect_zscore_outliers(
    series: pd.Series,
    threshold: float = 3.0,
) -> AnomalyReport:
    """Flag values where |z-score| > *threshold*."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 5:
        return AnomalyReport(
            column=str(series.name),
            method="zscore",
            outlier_count=0,
            total_count=len(numeric),
            outlier_pct=0.0,
        )
    mean = numeric.mean()
    std = numeric.std()
    if std == 0:
        return AnomalyReport(
            column=str(series.name), method="zscore",
            outlier_count=0, total_count=len(numeric), outlier_pct=0.0,
        )
    z = np.abs((numeric - mean) / std)
    outliers = int((z > threshold).sum())
    return AnomalyReport(
        column=str(series.name),
        method="zscore",
        outlier_count=outliers,
        total_count=len(numeric),
        outlier_pct=round(outliers / len(numeric) * 100, 2),
        details={"mean": float(mean), "std": float(std), "threshold": threshold},
    )


def detect_iqr_outliers(
    series: pd.Series,
    factor: float = 1.5,
) -> AnomalyReport:
    """Flag values outside Q1 − factor*IQR .. Q3 + factor*IQR."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 5:
        return AnomalyReport(
            column=str(series.name), method="iqr",
            outlier_count=0, total_count=len(numeric), outlier_pct=0.0,
        )
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    outliers = int(((numeric < lower) | (numeric > upper)).sum())
    return AnomalyReport(
        column=str(series.name),
        method="iqr",
        outlier_count=outliers,
        total_count=len(numeric),
        outlier_pct=round(outliers / len(numeric) * 100, 2),
        details={"q1": q1, "q3": q3, "iqr": iqr, "lower": lower, "upper": upper},
    )


def run_anomaly_scan(
    df: pd.DataFrame,
    columns: List[str] | None = None,
    method: str = "zscore",
) -> List[AnomalyReport]:
    """Scan selected numeric columns for anomalies."""
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    detect_fn = detect_zscore_outliers if method == "zscore" else detect_iqr_outliers
    reports: List[AnomalyReport] = []
    for col in columns:
        if col in df.columns:
            reports.append(detect_fn(df[col]))
    return reports


def detect_anomalies(
    df: pd.DataFrame,
    column: str,
    threshold: float = 3.0,
) -> List[int]:
    """Return list of row indices flagged as outliers by z-score."""
    if column not in df.columns:
        return []
    numeric = pd.to_numeric(df[column], errors="coerce").dropna()
    if len(numeric) < 5:
        return []
    mean = numeric.mean()
    std = numeric.std()
    if std == 0:
        return []
    z = np.abs((numeric - mean) / std)
    return numeric[z > threshold].index.tolist()
