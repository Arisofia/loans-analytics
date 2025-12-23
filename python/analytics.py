import pandas as pd
import numpy as np
from typing import Tuple, Dict
from python.validation import safe_numeric, REQUIRED_ANALYTICS_COLUMNS, validate_dataframe
from apps.analytics.src.enterprise_analytics_engine import LoanAnalyticsEngine

# Alias for backward compatibility if needed
standardize_numeric = safe_numeric

def calculate_quality_score(df: pd.DataFrame) -> float:
    """
    Calculate data quality score based on completeness (non-null values).
    Returns a score between 0 and 100.
    """
    if df.empty:
        return 0.0
    
    total_cells = df.size
    if total_cells == 0:
        return 0.0
        
    non_null_cells = df.count().sum()
    return (non_null_cells / total_cells) * 100.0

def project_growth(
    current_yield: float,
    target_yield: float,
    current_loan_volume: float,
    target_loan_volume: float,
    periods: int = 6
) -> pd.DataFrame:
    """
    Generate a linear projection for yield and loan volume growth.
    """
    if periods < 2:
        raise ValueError("periods must be at least 2")
        
    dates = pd.date_range(start=pd.Timestamp.now(), periods=periods, freq="MS")
    
    yields = np.linspace(current_yield, target_yield, periods)
    volumes = np.linspace(current_loan_volume, target_loan_volume, periods)
    
    return pd.DataFrame({
        "date": dates,
        "yield": yields,
        "loan_volume": volumes
    })

def portfolio_kpis(df: pd.DataFrame) -> Tuple[Dict[str, float], pd.DataFrame]:
    """
    Calculate portfolio-level KPIs and enrich DataFrame with ratios.
    """
    enriched = df.copy()
    metrics = {
        "delinquency_rate": 0.0,
        "portfolio_yield": 0.0,
        "average_ltv": 0.0,
        "average_dti": 0.0,
    }
    
    if enriched.empty:
        return metrics, enriched

    validate_dataframe(enriched, required_columns=REQUIRED_ANALYTICS_COLUMNS)

    # Use Enterprise Engine for standardized calculation
    engine = LoanAnalyticsEngine(enriched)
    
    # Enrich DataFrame with calculated ratios
    enriched["ltv_ratio"] = engine.compute_loan_to_value()
    enriched["dti_ratio"] = engine.compute_debt_to_income()

    # Get standardized KPIs
    results = engine.run_full_analysis()
    metrics["delinquency_rate"] = results["portfolio_delinquency_rate_percent"]
    metrics["portfolio_yield"] = results["portfolio_yield_percent"]
    metrics["average_ltv"] = results["average_ltv_ratio_percent"]
    metrics["average_dti"] = results["average_dti_ratio_percent"]
    
    # Fill NaNs in metrics
    for k in metrics:
        if pd.isna(metrics[k]):
            metrics[k] = 0.0
            
    return metrics, enriched