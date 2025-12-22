from datetime import datetime

import pandas as pd
import pytest

from src.enterprise_analytics_engine import LoanAnalyticsConfig, LoanAnalyticsEngine


@pytest.fixture()
def sample_loan_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "loan_id": "L1",
                "principal": 10000,
                "interest_rate": 0.1,
                "term_months": 24,
                "origination_date": datetime(2022, 1, 15),
                "status": "current",
                "days_in_arrears": 0,
                "balance": 8000,
                "payments_made": 2000,
                "write_off_amount": 0,
                "region": "NA",
                "product": "A",
                "currency": "USD",
            },
            {
                "loan_id": "L2",
                "principal": 5000,
                "interest_rate": 0.12,
                "term_months": 12,
                "origination_date": datetime(2022, 2, 10),
                "status": None,
                "days_in_arrears": 120,
                "balance": 4500,
                "payments_made": 500,
                "write_off_amount": 0,
                "region": "EU",
                "product": "B",
                "currency": "USD",
            },
            {
                "loan_id": "L3",
                "principal": 7000,
                "interest_rate": 0.15,
                "term_months": 18,
                "origination_date": datetime(2021, 11, 20),
                "status": "DEFAULT",
                "days_in_arrears": 200,
                "balance": 0,
                "payments_made": 5000,
                "write_off_amount": 2000,
                "region": "NA",
                "product": "B",
                "currency": "USD",
            },
            {
                "loan_id": "L4",
                "principal": 6000,
                "interest_rate": 0.08,
                "term_months": 12,
                "origination_date": datetime(2022, 3, 10),
                "status": "prepaid",
                "days_in_arrears": 0,
                "balance": 0,
                "payments_made": 6000,
                "write_off_amount": 0,
                "region": "SA",
                "product": "A",
                "currency": "USD",
            },
        ]
    )


def test_missing_columns_raise_value_error(sample_loan_data: pd.DataFrame):
    truncated = sample_loan_data.drop(columns=["principal"])
    with pytest.raises(ValueError):
        LoanAnalyticsEngine(truncated)


def test_invalid_origination_dates_raise(sample_loan_data: pd.DataFrame):
    invalid = sample_loan_data.copy()
    invalid.loc[0, "origination_date"] = "not-a-date"
    with pytest.raises(ValueError):
        LoanAnalyticsEngine(invalid)


def test_arrears_flag_defaults_to_days_threshold(sample_frame: pd.DataFrame):
    engine = LoanAnalyticsEngine(sample_frame, config=LoanAnalyticsConfig(arrears_threshold=90))
    arrears_series = engine.data.loc[engine.data["loan_id"] == "L2", "arrears_flag"]
    assert len(arrears_series) == 1, "Expected exactly one loan with loan_id 'L2'"
    arrears = arrears_series.iloc[0]
    assert bool(arrears) is True
    arrears_series = engine.data.loc[engine.data["loan_id"] == "L2", "arrears_flag"]
    assert not arrears_series.empty, "Expected at least one loan with loan_id 'L2'"
    arrears = arrears_series.iloc[0]
    assert bool(arrears) is True


def test_portfolio_kpis(sample_frame: pd.DataFrame):
    engine = LoanAnalyticsEngine(sample_frame)
    kpis = engine.portfolio_kpis()

    assert kpis["currency"] == "USD"
    assert kpis["exposure"] == pytest.approx(28_000)
    expected_weighted_interest_rate = (0.1 * 10000 + 0.12 * 5000 + 0.15 * 7000 + 0.08 * 6000) / 28000
    assert kpis["weighted_interest_rate"] == pytest.approx(expected_weighted_interest_rate)
    assert kpis["npl_ratio"] == pytest.approx((5000 + 7000) / 28000)
    assert kpis["default_rate"] == pytest.approx(7000 / 28000)
    assert kpis["lgd"] == pytest.approx(2000 / 7000)
    assert kpis["prepayment_rate"] == pytest.approx(6000 / 28000)
    assert kpis["repayment_velocity"] == pytest.approx(13_500 / 28_000)


def test_segment_kpis_by_region(sample_frame: pd.DataFrame):
    engine = LoanAnalyticsEngine(sample_frame)
    segment_df = engine.segment_kpis("region")

    assert set(segment_df["region"]) == {"NA", "EU", "SA"}
    na_rows = segment_df.loc[segment_df["region"] == "NA"]
    assert not na_rows.empty
    na_row = na_rows.iloc[0]
    assert na_row["exposure"] == pytest.approx(17_000)
    assert na_row["default_rate"] == pytest.approx(7000 / 17_000)


def test_vintage_default_table_sorted(sample_frame: pd.DataFrame):
    engine = LoanAnalyticsEngine(sample_frame)
    vintage = engine.vintage_default_table()

    assert list(vintage["origination_quarter"]) == sorted(vintage["origination_quarter"].tolist())
    row = vintage.loc[vintage["origination_quarter"] == "2021Q4"].iloc[0]
    assert row["default_rate"] == pytest.approx(1.0)


def test_cashflow_curve_shape(sample_frame: pd.DataFrame):
    engine = LoanAnalyticsEngine(sample_frame)
    curve = engine.cashflow_curve(freq="Q")

    assert not curve.empty
    assert curve["cumulative_cashflow"].iloc[-1] == pytest.approx(curve["cashflow"].sum())
    assert curve.shape[1] == 3
