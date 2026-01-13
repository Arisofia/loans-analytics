import pandas as pd
import pytest
from src.pipeline.data_ingestion import UnifiedIngestion


def test_ingest_csv(tmp_path, minimal_config):
    csv_content = "measurement_date,total_receivable_usd,total_eligible_usd,discounted_balance_usd,dpd_0_7_usd,dpd_7_30_usd,dpd_30_60_usd,dpd_60_90_usd,dpd_90_plus_usd,cash_available_usd\n2025-12-01,1000.0,800,700,100,100,100,100,100,500\n2025-12-02,2000.0,1600,1400,200,200,200,200,200,1000"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    ingestion = UnifiedIngestion(minimal_config)
    result = ingestion.ingest_file(csv_file)
    assert not result.df.empty
    assert result.run_id == ingestion.run_id
    assert isinstance(result.df, pd.DataFrame)
    assert result.df["total_receivable_usd"].sum() == pytest.approx(3000.0)


def test_ingest_csv_error(tmp_path, minimal_config):
    ingestion = UnifiedIngestion(minimal_config)
    with pytest.raises(FileNotFoundError):
        ingestion.ingest_file(tmp_path / "nonexistent.csv")


def test_ingest_csv_empty_file(tmp_path, minimal_config):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")
    ingestion = UnifiedIngestion(minimal_config)
    with pytest.raises(Exception):
        ingestion.ingest_file(csv_file)


def test_ingest_csv_strict_schema_failure(tmp_path, minimal_config):
    csv_content = "measurement_date,total_receivable_usd\n2025-12-01,1000.0"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    minimal_config["pipeline"]["phases"]["ingestion"]["validation"]["strict"] = True
    ingestion = UnifiedIngestion(minimal_config)
    with pytest.raises(Exception):
        ingestion.ingest_file(csv_file)


def test_ingest_csv_success(tmp_path, minimal_config):
    csv_content = "measurement_date,total_receivable_usd,total_eligible_usd,discounted_balance_usd,cash_available_usd,dpd_0_7_usd,dpd_7_30_usd,dpd_30_60_usd,dpd_60_90_usd,dpd_90_plus_usd\n2025-12-01,1000.0,800,700,500,100,100,100,100,100"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    ingestion = UnifiedIngestion(minimal_config)
    result = ingestion.ingest_file(csv_file)
    assert result.df is not None
    assert len(result.df) == 1


def test_ingest_http(minimal_config):
    ingestion = UnifiedIngestion(minimal_config)
    with pytest.raises(Exception):
        ingestion.ingest_http("http://nonexistent-url.invalid/data.csv")


def test_run_id_generation(minimal_config):
    ingestion1 = UnifiedIngestion(minimal_config)
    ingestion2 = UnifiedIngestion(minimal_config)
    assert ingestion1.run_id != ingestion2.run_id
    assert ingestion1.run_id.startswith("ingest_")
    assert ingestion2.run_id.startswith("ingest_")


def test_audit_log_creation(tmp_path, minimal_config):
    csv_content = "measurement_date,total_receivable_usd,total_eligible_usd,discounted_balance_usd,cash_available_usd,dpd_0_7_usd,dpd_7_30_usd,dpd_30_60_usd,dpd_60_90_usd,dpd_90_plus_usd\n2025-12-01,1000.0,800,700,500,100,100,100,100,100"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    ingestion = UnifiedIngestion(minimal_config)
    ingestion.ingest_file(csv_file)
    assert len(ingestion.audit_log) > 0
    assert any(entry["event"] == "start" for entry in ingestion.audit_log)
    assert any(entry["event"] == "complete" for entry in ingestion.audit_log)


def test_looker_par_balances_to_loan_tape(tmp_path, minimal_config):
    """Test conversion of Looker PAR balance data to loan tape format."""
    par_csv = """reporting_date,outstanding_balance_usd,par_7_balance_usd,par_30_balance_usd,par_60_balance_usd,par_90_balance_usd
2025-12-01,10000.0,500.0,300.0,200.0,100.0
2025-12-02,15000.0,750.0,450.0,300.0,150.0"""
    csv_file = tmp_path / "par_balances.csv"
    csv_file.write_text(par_csv)

    ingestion = UnifiedIngestion(minimal_config)
    df = pd.read_csv(csv_file)
    cash_by_date = {}
    result = ingestion._looker_par_balances_to_loan_tape(df, cash_by_date)

    assert "measurement_date" in result.columns
    assert "total_receivable_usd" in result.columns
    assert "dpd_90_plus_usd" in result.columns
    assert "dpd_60_90_usd" in result.columns
    assert "dpd_30_60_usd" in result.columns
    assert "dpd_7_30_usd" in result.columns
    assert "dpd_0_7_usd" in result.columns
    assert result["total_receivable_usd"].iloc[0] == pytest.approx(10000.0)
    assert result["dpd_90_plus_usd"].iloc[0] == pytest.approx(100.0)
    assert result["dpd_60_90_usd"].iloc[0] == pytest.approx(200.0 - 100.0)


def test_looker_dpd_to_loan_tape(tmp_path, minimal_config):
    """Test conversion of Looker DPD-based loan data to loan tape format."""
    dpd_csv = """dpd,outstanding_balance_usd,disburse_date
0,1000.0,2025-01-01
15,500.0,2025-01-02
45,300.0,2025-01-03
75,200.0,2025-01-04
95,100.0,2025-01-05"""
    csv_file = tmp_path / "loans_dpd.csv"
    csv_file.write_text(dpd_csv)

    ingestion = UnifiedIngestion(minimal_config)
    df = pd.read_csv(csv_file)
    cash_by_date = {}
    result = ingestion._looker_dpd_to_loan_tape(df, cash_by_date)

    assert "dpd_0_7_usd" in result.columns
    assert "dpd_7_30_usd" in result.columns
    assert "dpd_30_60_usd" in result.columns
    assert "dpd_60_90_usd" in result.columns
    assert "dpd_90_plus_usd" in result.columns
    assert len(result) == 1
    assert result["dpd_0_7_usd"].iloc[0] == pytest.approx(1000.0)
    assert result["dpd_7_30_usd"].iloc[0] == pytest.approx(500.0)
    assert result["dpd_30_60_usd"].iloc[0] == pytest.approx(300.0)
    assert result["dpd_60_90_usd"].iloc[0] == pytest.approx(200.0)
    assert result["dpd_90_plus_usd"].iloc[0] == pytest.approx(100.0)


def test_ingest_looker_with_par_balances(tmp_path, minimal_config):
    """Test Looker ingestion with PAR balance data."""
    par_csv = """reporting_date,outstanding_balance_usd,par_7_balance_usd,par_30_balance_usd,par_60_balance_usd,par_90_balance_usd
2025-12-01,10000.0,500.0,300.0,200.0,100.0"""
    loans_file = tmp_path / "par_balances.csv"
    loans_file.write_text(par_csv)

    ingestion = UnifiedIngestion(minimal_config)
    result = ingestion.ingest_looker(loans_file)

    assert isinstance(result.df, pd.DataFrame)
    assert not result.df.empty
    assert "measurement_date" in result.df.columns
    assert "total_receivable_usd" in result.df.columns
    assert result.df["total_receivable_usd"].iloc[0] == pytest.approx(10000.0)


def test_ingest_looker_with_dpd_data(tmp_path, minimal_config):
    """Test Looker ingestion with DPD-based loan data."""
    dpd_csv = """dpd,outstanding_balance_usd
10,1000.0
50,500.0"""
    loans_file = tmp_path / "loans_dpd.csv"
    loans_file.write_text(dpd_csv)

    ingestion = UnifiedIngestion(minimal_config)
    result = ingestion.ingest_looker(loans_file)

    assert isinstance(result.df, pd.DataFrame)
    assert not result.df.empty
    assert "dpd_7_30_usd" in result.df.columns
    assert "dpd_30_60_usd" in result.df.columns
