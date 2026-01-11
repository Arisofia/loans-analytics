import pandas as pd
import pytest
from pipeline.ingestion import UnifiedIngestion


@pytest.fixture
def base_config():
    return {"pipeline": {"phases": {"ingestion": {"validation": {"strict": False}}}}}


def make_loans(dates, disburse_dates=None, maturity_dates=None, dpd_vals=None, balances=None):
    data = {
        "dpd": dpd_vals or [0] * len(dates),
        "outstanding_balance": balances or [10] * len(dates),
    }
    if disburse_dates is not None:
        data["disburse_date"] = disburse_dates
    if maturity_dates is not None:
        data["maturity_date"] = maturity_dates
    return pd.DataFrame(data)


def test_measurement_strategy_max_disburse_date(base_config):
    # Loans with different disburse dates; strategy should set measurement_date to max disburse_date
    loans = make_loans(
        dates=["x", "y"],
        disburse_dates=["2023-01-01", "2023-02-01"],
        dpd_vals=[0, 10],
        balances=[100, 50],
    )
    cfg = base_config.copy()
    cfg["pipeline"]["phases"]["ingestion"]["looker"] = {
        "measurement_date_strategy": "max_disburse_date"
    }
    ui = UnifiedIngestion(cfg)
    result = ui._looker_dpd_to_loan_tape(loans, {})
    assert result["measurement_date"].iloc[0].startswith("2023-02-01")


def test_measurement_strategy_max_maturity_date(base_config):
    loans = make_loans(
        dates=["x", "y"],
        maturity_dates=["2024-01-01", "2024-03-01"],
        dpd_vals=[0, 40],
        balances=[100, 200],
    )
    cfg = base_config.copy()
    cfg["pipeline"]["phases"]["ingestion"]["looker"] = {
        "measurement_date_strategy": "max_maturity_date"
    }
    ui = UnifiedIngestion(cfg)
    result = ui._looker_dpd_to_loan_tape(loans, {})
    assert result["measurement_date"].iloc[0].startswith("2024-03-01")


def test_measurement_date_column_takes_precedence(base_config):
    loans = pd.DataFrame(
        {"days_past_due": [5], "outstanding_balance": [50], "as_of_date": ["2022-12-12"]}
    )
    cfg = base_config.copy()
    cfg["pipeline"]["phases"]["ingestion"]["looker"] = {"measurement_date_column": "as_of_date"}
    ui = UnifiedIngestion(cfg)
    result = ui._looker_dpd_to_loan_tape(loans, {})
    assert result["measurement_date"].iloc[0].startswith("2022-12-12")
