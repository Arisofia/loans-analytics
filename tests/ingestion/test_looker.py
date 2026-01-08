import time
import pandas as pd
import pytest
from src.pipeline.data_ingestion import UnifiedIngestion


@pytest.fixture
def base_config():
    return {"pipeline": {"phases": {"ingestion": {"validation": {"strict": False}}}}}


def test_measurement_strategy_max_disburse_date(base_config):
    loans = pd.DataFrame(
        {
            "dpd": [0, 10],
            "outstanding_balance": [100, 50],
            "disburse_date": ["2023-01-01", "2023-02-01"],
        }
    )
    cfg = base_config.copy()
    cfg["pipeline"]["phases"]["ingestion"]["looker"] = {
        "measurement_date_strategy": "max_disburse_date"
    }
    ui = UnifiedIngestion(cfg)
    # The new implementation uses looker_converter.convert_dpd_loans
    result = ui.looker_converter.convert_dpd_loans(loans, {})
    assert result["measurement_date"].iloc[0] == "2023-02-01"


def test_load_looker_financials_selects_latest(tmp_path):
    ui = UnifiedIngestion({"pipeline": {"phases": {"ingestion": {}}}})
    d = tmp_path / "fin"
    d.mkdir()
    # older file
    (d / "old.csv").write_text("reporting_date,cash_balance_usd\n2023-01-01,10\n")
    time.sleep(0.1)
    # newer file
    (d / "new.csv").write_text("reporting_date,cash_balance_usd\n2023-02-01,20\n")

    result, meta = ui.looker_converter.load_financials(d)
    assert "2023-02-01" in result
    assert result["2023-02-01"]["cash_balance_usd"] == 20.0


def test_looker_par_balances_to_loan_tape(base_config):
    ui = UnifiedIngestion(base_config)
    df = pd.DataFrame(
        {
            "reporting_date": ["2024-01-01", "2024-01-01"],
            "outstanding_balance_usd": [100.0, 50.0],
            "par_7_balance_usd": [20.0, 10.0],
            "par_30_balance_usd": [10.0, 5.0],
            "par_60_balance_usd": [5.0, 2.0],
            "par_90_balance_usd": [2.0, 1.0],
        }
    )
    cash_by_date = {"2024-01-01": {"cash_balance_usd": 15.0}}
    out = ui.looker_converter.convert_par_balances(df, cash_by_date)
    assert "measurement_date" in out.columns
    assert out["total_receivable_usd"].sum() == pytest.approx(150.0)
    row = out.loc[out["measurement_date"] == "2024-01-01"].iloc[0]
    assert row["cash_available_usd"] == pytest.approx(15.0)


def test_looker_dpd_to_loan_tape(base_config):
    ui = UnifiedIngestion(base_config)
    df = pd.DataFrame(
        {"dpd": [0, 5, 10, 40, 75, 120], "outstanding_balance": [10, 10, 10, 10, 10, 10]}
    )
    out = ui.looker_converter.convert_dpd_loans(df, {})
    assert out["dpd_0_7_usd"].sum() >= 10.0
    assert out["dpd_7_30_usd"].sum() >= 10.0
    assert out["dpd_30_60_usd"].sum() >= 10.0
    assert out["dpd_60_90_usd"].sum() >= 10.0 or out["dpd_90_plus_usd"].sum() >= 10.0


def test_ingest_looker_missing_columns_raises(tmp_path, base_config):
    ui = UnifiedIngestion(base_config)
    p = tmp_path / "loans.csv"
    p.write_text("loan_id,outstanding_balance\n1,100\n")

    with pytest.raises(ValueError, match="missing required PAR or DPD columns"):
        ui.ingest_looker(p)
