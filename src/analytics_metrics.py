import numpy as np
import pandas as pd

CURRENCY_SYMBOLS = r"[₡$€£¥₽%]"


def standardize_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(CURRENCY_SYMBOLS, "", regex=True)
        .str.replace(",", "", regex=False)
        .replace({"": np.nan, "nan": np.nan})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def project_growth(
    current_yield: float,
    target_yield: float,
    current_loan_volume: float,
    target_loan_volume: float,
    periods: int = 6,
) -> pd.DataFrame:
    """Project portfolio yield and loan volume over a monthly horizon."""

    if periods < 2:
        raise ValueError("periods must be at least 2 to create a projection range")

    schedule = pd.date_range(pd.Timestamp.now().normalize(), periods=periods, freq="MS")
    projection = pd.DataFrame(
        {
            "month": schedule,
            "yield": np.linspace(current_yield, target_yield, periods),
            "loan_volume": np.linspace(current_loan_volume, target_loan_volume, periods),
        }
    )

    total_principal = enriched["principal_balance"].sum()
    delinquent_principal = enriched.loc[
        enriched["loan_status"].astype(str).str.lower() == "delinquent",
        "principal_balance",
    ].sum()
    delinquency_rate = delinquent_principal / total_principal if total_principal else 0.0

    weighted_interest = (enriched["principal_balance"] * enriched["interest_rate"]).sum()
    portfolio_yield = weighted_interest / total_principal if total_principal else 0.0

    average_ltv = enriched["ltv_ratio"].mean() if not enriched["ltv_ratio"].empty else 0.0
    average_dti = float(np.nan_to_num(enriched["dti_ratio"].mean(skipna=True), nan=0.0))

    metrics = {
        "delinquency_rate": float(delinquency_rate),
        "portfolio_yield": float(portfolio_yield),
        "average_ltv": float(average_ltv) if not np.isnan(average_ltv) else 0.0,
        "average_dti": average_dti,
    }
    return metrics, enriched
