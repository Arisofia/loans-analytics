import pandas as pd
import pytest

from src.analytics_metrics import calculate_quality_score, portfolio_kpis, project_growth, standardize_numeric


def sample_df():
    return pd.DataFrame(
        {
            "loan_amount": [100000, 200000, 150000],
            "appraised_value": [125000, 210000, 180000],
            "borrower_income": [60000, 80000, 75000],
            "monthly_debt": [1200, 1800, 1500],
            "loan_status": ["current", "30-59 days past due", "current"],
            "principal_balance": [90000, 195000, 140000],
            "interest_rate": [0.05, 0.06, 0.055],
        }
    )


def test_standardize_numeric_handles_symbols():
    series = pd.Series(
        [
            "$1,200",
            "€2,500",
            "25%",
            "£3,000",
            "¥4,500",
            "₽5,500",
            "",
            "nan",
            "abc",
            None,
            " 7,500 ",
        ]
    )
    cleaned = standardize_numeric(series)
    assert cleaned.iloc[0] == 1200.0
    assert cleaned.iloc[1] == 2500.0
    assert cleaned.iloc[3] == 3000.0
    assert cleaned.iloc[4] == 4500.0
    assert cleaned.iloc[5] == 5500.0
    assert cleaned.iloc[2] == 25.0
    assert pd.isna(cleaned.iloc[6])
    assert pd.isna(cleaned.iloc[7])
    assert pd.isna(cleaned.iloc[8])
    assert pd.isna(cleaned.iloc[9])
    assert cleaned.iloc[10] == 7500.0


def test_calculate_quality_score_rewards_complete_data():
    df = sample_df()
    score = calculate_quality_score(df)
    assert isinstance(score, int)
    assert score == 100

    df_with_missing = df.copy()
    df_with_missing.loc[0, "loan_amount"] = None
    penalized_score = calculate_quality_score(df_with_missing)
    assert isinstance(penalized_score, int)
    assert penalized_score < 100


def test_calculate_quality_score_empty_dataframe_returns_zero():
    empty_df = pd.DataFrame(columns=sample_df().columns)
    score = calculate_quality_score(empty_df)
    assert isinstance(score, int)
    assert score == 0


def test_calculate_quality_score_is_clamped_at_zero():
    df = sample_df().copy()
    for col in df.columns:
        df[col] = None
    for i in range(5):
        df[f"extra_{i}"] = None

    score = calculate_quality_score(df)
    assert isinstance(score, int)
    assert score == 0


def test_portfolio_kpis_returns_expected_metrics():
    metrics, enriched = portfolio_kpis(sample_df())
    assert set(metrics.keys()) == {"delinquency_rate", "portfolio_yield", "average_ltv", "average_dti"}
    assert "ltv_ratio" in enriched.columns
    assert "dti_ratio" in enriched.columns


def test_portfolio_kpis_missing_column_raises():
    df = sample_df().drop(columns=["loan_amount"])
    with pytest.raises(ValueError, match="Missing required columns: loan_amount"):
        portfolio_kpis(df)


def test_portfolio_kpis_handles_empty_frame():
    df = sample_df().iloc[:0]
    metrics, enriched = portfolio_kpis(df)
    assert metrics == {
        "delinquency_rate": 0.0,
        "portfolio_yield": 0.0,
        "average_ltv": 0.0,
        "average_dti": 0.0,
    }
    assert enriched.empty


def test_portfolio_kpis_zero_principal_yield_is_zero():
    df = sample_df()
    df["principal_balance"] = 0
    metrics, _ = portfolio_kpis(df)
    assert metrics["portfolio_yield"] == 0.0


def test_portfolio_kpis_dti_nan_when_income_non_positive():
    df = sample_df()
    df["borrower_income"] = [0, -5000, 0]
    metrics, enriched = portfolio_kpis(df)
    assert enriched["dti_ratio"].isna().all()
    assert metrics["average_dti"] == 0.0


def test_portfolio_kpis_ltv_nan_when_appraisal_non_positive():
    df = sample_df()
    df["appraised_value"] = [0, -100000, 0]
    metrics, enriched = portfolio_kpis(df)
    assert enriched["ltv_ratio"].isna().all()
    assert metrics["average_ltv"] == 0.0


def test_project_growth_builds_monotonic_path():
    projection = project_growth(1.0, 2.0, 100, 200, periods=4)
    assert len(projection) == 4
    assert projection["yield"].iloc[0] == 1.0
    assert projection["yield"].iloc[-1] == 2.0
    assert projection["loan_volume"].iloc[0] == 100
    assert projection["loan_volume"].iloc[-1] == 200
    assert pd.api.types.is_datetime64_any_dtype(projection["date"])


def test_project_growth_rejects_insufficient_periods():
    with pytest.raises(ValueError, match="periods must be at least 2"):
        project_growth(1.0, 2.0, 100, 200, periods=1)


def test_project_growth_formats_month_labels():
    projection = project_growth(1.0, 1.5, 100, 120, periods=3)
    assert projection["month"].str.match(r"^[A-Z][a-z]{2} \d{4}$").all()


def test_project_growth_supports_decreasing_targets():
    projection = project_growth(2.0, 1.0, 200, 100, periods=3)
    assert projection["yield"].is_monotonic_decreasing
    assert projection["loan_volume"].is_monotonic_decreasing
