import pandas as pd
import numpy as np
from typing import Tuple, Dict
from python.validation import safe_numeric

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

    required = ["loan_amount", "appraised_value", "borrower_income", "monthly_debt", "principal_balance", "interest_rate", "loan_status"]
    missing = [c for c in required if c not in enriched.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    # Enrich with safe division
    enriched["ltv_ratio"] = np.where(enriched["appraised_value"] > 0, enriched["loan_amount"] / enriched["appraised_value"] * 100, 0.0)
    enriched["dti_ratio"] = np.where(enriched["borrower_income"] > 0, enriched["monthly_debt"] / (enriched["borrower_income"] / 12) * 100, np.nan)

    # Metrics
    total_principal = enriched["principal_balance"].sum()
    
    if total_principal > 0:
        delinquent_principal = enriched.loc[
            enriched["loan_status"].astype(str).str.lower() == "delinquent",
            "principal_balance"
        ].sum()
        metrics["delinquency_rate"] = (delinquent_principal / total_principal)
        metrics["portfolio_yield"] = (enriched["principal_balance"] * enriched["interest_rate"]).sum() / total_principal

    metrics["average_ltv"] = enriched["ltv_ratio"].mean()
    metrics["average_dti"] = enriched["dti_ratio"].mean()
    
    # Fill NaNs in metrics
    for k in metrics:
        if pd.isna(metrics[k]):
            metrics[k] = 0.0
            
    return metrics, enriched