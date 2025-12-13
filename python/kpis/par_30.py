
import pandas as pd

def calculate_par_30(df: pd.DataFrame) -> float:
    """Portfolio at Risk (30+ days)
    Formula: SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable)
    """
    required = ['dpd_30_60_usd', 'dpd_60_90_usd', 'dpd_90_plus_usd', 'total_receivable_usd']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"PAR_30 calculation failed: missing columns: {missing}")

    dpd_30_plus = (
        df['dpd_30_60_usd'].sum() +
        df['dpd_60_90_usd'].sum() +
        df['dpd_90_plus_usd'].sum()
    )
    total_receivable = df['total_receivable_usd'].sum()
    if not pd.api.types.is_numeric_dtype(df['total_receivable_usd']):
        raise ValueError("PAR_30 calculation failed: total_receivable_usd is not numeric")
        
    par_30 = (
        dpd_30_plus / total_receivable * 100
        if total_receivable > 0
        else 0
    )
    return par_30
