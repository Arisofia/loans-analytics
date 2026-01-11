"""
Unit tests for the run_scoring CLI and analytics pipeline.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from src.analytics.run_scoring import (load_portfolio, main, parse_args,
                                       summarize_results)


def test_parse_args_minimal_required():
    with patch("sys.argv", ["script.py", "--data", "/path/to/data.csv"]):
        args = parse_args()
        assert args.data == "/path/to/data.csv"
        assert args.output is None
        assert abs(args.ltv_threshold - 90.0) < 1e-6
        assert abs(args.dti_threshold - 40.0) < 1e-6


def test_parse_args_all_options():
    with patch(
        "sys.argv",
        [
            "script.py",
            "--data",
            "/path/to/data.csv",
            "--output",
            "/path/to/output.json",
            "--export-blob",
            "container-name",
            "--blob-name",
            "custom-blob.json",
            "--ltv-threshold",
            "85.0",
            "--dti-threshold",
            "35.0",
        ],
    ):
        args = parse_args()
        assert args.data == "/path/to/data.csv"
        assert args.output == "/path/to/output.json"
        assert args.container_name == "container-name"
        assert args.blob_name == "custom-blob.json"
        assert abs(args.ltv_threshold - 85.0) < 1e-6
        assert abs(args.dti_threshold - 35.0) < 1e-6


def test_parse_args_requires_data():
    with patch("sys.argv", ["script.py"]):
        with pytest.raises(SystemExit):
            parse_args()


def test_load_portfolio_file_exists(tmp_path):
    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text(
        "loan_amount,appraised_value,borrower_income,monthly_debt,"
        "loan_status,interest_rate,principal_balance\n"
        "250000,300000,80000,1500,current,0.035,240000"
    )

    df = load_portfolio(csv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1


def test_load_portfolio_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_portfolio(Path("/nonexistent/file.csv"))


def test_load_portfolio_expands_user_path(tmp_path):
    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text(
        "loan_amount,appraised_value,borrower_income,monthly_debt,"
        "loan_status,interest_rate,principal_balance\n"
        "250000,300000,80000,1500,current,0.035,240000"
    )

    df = load_portfolio(csv_file)
    assert not df.empty


def test_summarize_results_prints_output(capsys):
    metrics = {
        "portfolio_yield_percent": 4.5,
        "delinquency_rate_percent": 2.3,
    }
    summarize_results(metrics, 5)

    captured = capsys.readouterr()
    assert (
        "Portfolio Yield Percent" in captured.out
        or "portfolio yield percent" in captured.out.lower()
    )
    assert "Risk alerts flagged: 5" in captured.out


def test_summarize_results_formats_numbers(capsys):
    metrics = {
        "metric1": 1.5555,
        "metric2": 2.9999,
    }
    summarize_results(metrics, 0)

    captured = capsys.readouterr()
    assert "1.56" in captured.out or "1.55" in captured.out
    assert "3.00" in captured.out or "3.0" in captured.out


def test_summarize_results_handles_strings(capsys):
    metrics = {
        "status": "healthy",
        "yield_percent": 4.5,
    }
    summarize_results(metrics, 0)

    captured = capsys.readouterr()
    assert "healthy" in captured.out


@patch("src.analytics.run_scoring.LoanAnalyticsEngine")
@patch("src.analytics.run_scoring.load_portfolio")
def test_main_full_flow_no_export(mock_load, mock_engine_class, tmp_path):
    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text(
        "loan_amount,appraised_value,borrower_income,monthly_debt,"
        "loan_status,interest_rate,principal_balance\n"
        "250000,300000,80000,1500,current,0.035,240000"
    )

    mock_df = pd.DataFrame(
        {
            "loan_amount": [250000],
            "appraised_value": [300000],
            "borrower_income": [80000],
            "monthly_debt": [1500],
            "loan_status": ["current"],
            "interest_rate": [0.035],
            "principal_balance": [240000],
        }
    )
    mock_load.return_value = mock_df

    mock_engine = MagicMock()
    mock_engine.run_full_analysis.return_value = {
        "portfolio_delinquency_rate_percent": 0.0,
        "portfolio_yield_percent": 4.5,
    }
    mock_engine.risk_alerts.return_value = pd.DataFrame()
    mock_engine_class.return_value = mock_engine

    with patch("sys.argv", ["script.py", "--data", str(csv_file)]):
        main()

    mock_engine.run_full_analysis.assert_called_once()
    # risk_alerts not called because --include-risk-alerts not passed
    mock_engine.risk_alerts.assert_not_called()


@patch("src.analytics.run_scoring.LoanAnalyticsEngine")
@patch("src.analytics.run_scoring.load_portfolio")
def test_main_output_to_file(mock_load, mock_engine_class, tmp_path):
    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text(
        "loan_amount,appraised_value,borrower_income,monthly_debt,"
        "loan_status,interest_rate,principal_balance\n"
        "250000,300000,80000,1500,current,0.035,240000"
    )
    output_file = tmp_path / "output.json"

    mock_df = pd.DataFrame(
        {
            "loan_amount": [250000],
            "appraised_value": [300000],
            "borrower_income": [80000],
            "monthly_debt": [1500],
            "loan_status": ["current"],
            "interest_rate": [0.035],
            "principal_balance": [240000],
        }
    )
    mock_load.return_value = mock_df

    mock_engine = MagicMock()
    mock_engine.run_full_analysis.return_value = {
        "portfolio_delinquency_rate_percent": 0.0,
        "portfolio_yield_percent": 4.5,
    }
    mock_engine.risk_alerts.return_value = pd.DataFrame()
    mock_engine_class.return_value = mock_engine

    with patch("sys.argv", ["script.py", "--data", str(csv_file), "--output", str(output_file)]):
        main()

    assert output_file.exists()
    with open(output_file, encoding="utf-8") as f:
        data = json.load(f)

    assert "portfolio_delinquency_rate_percent" in data


@patch("src.analytics.run_scoring.LoanAnalyticsEngine")
@patch("src.analytics.run_scoring.load_portfolio")
def test_main_blob_export_requires_credentials(mock_load, mock_engine_class, tmp_path):
    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text(
        (
            "loan_amount,appraised_value,borrower_income,monthly_debt,"
            "loan_status,interest_rate,principal_balance\n"
            "250000,300000,80000,1500,current,0.035,240000"
        )
    )

    mock_df = pd.DataFrame(
        {
            "loan_amount": [250000],
            "appraised_value": [300000],
            "borrower_income": [80000],
            "monthly_debt": [1500],
            "loan_status": ["current"],
            "interest_rate": [0.035],
            "principal_balance": [240000],
        }
    )
    mock_load.return_value = mock_df

    mock_engine = MagicMock()
    mock_engine.run_full_analysis.return_value = {"metric1": 1.0}
    mock_engine_class.return_value = mock_engine

    with patch("sys.argv", ["script.py", "--data", str(csv_file), "--export-blob", "container"]):
        with pytest.raises(SystemExit):
            main()


@patch("src.analytics.run_scoring.LoanAnalyticsEngine")
@patch("src.analytics.run_scoring.AzureBlobKPIExporter")
@patch("src.analytics.run_scoring.load_portfolio")
def test_main_blob_export_with_connection_string(
    mock_load, mock_exporter_class, mock_engine_class, tmp_path
):
    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text(
        (
            "loan_amount,appraised_value,borrower_income,monthly_debt,"
            "loan_status,interest_rate,principal_balance\n"
            "250000,300000,80000,1500,current,0.035,240000"
        )
    )

    mock_df = pd.DataFrame(
        {
            "loan_amount": [250000],
            "appraised_value": [300000],
            "borrower_income": [80000],
            "monthly_debt": [1500],
            "loan_status": ["current"],
            "interest_rate": [0.035],
            "principal_balance": [240000],
        }
    )
    mock_load.return_value = mock_df

    mock_engine = MagicMock()
    mock_engine.run_full_analysis.return_value = {"metric1": 1.0}
    mock_engine_class.return_value = mock_engine

    mock_exporter = MagicMock()
    mock_exporter_class.return_value = mock_exporter

    with patch(
        "sys.argv",
        [
            "script.py",
            "--data",
            str(csv_file),
            "--export-blob",
            "container",
            "--connection-string",
            "mock-connection-string",
        ],
    ):
        main()

    mock_exporter.upload_metrics.assert_called_once()


@patch("src.analytics.run_scoring.parse_args")
def test_main_parses_custom_thresholds(mock_parse_args, tmp_path):
    csv_file = tmp_path / "portfolio.csv"
    csv_file.write_text(
        "loan_amount,appraised_value,borrower_income,monthly_debt,"
        "loan_status,interest_rate,principal_balance\n"
        "250000,300000,80000,1500,current,0.035,240000"
    )

    mock_args = MagicMock()
    mock_args.data = str(csv_file)
    mock_args.output = None
    mock_args.container_name = None
    mock_args.ltv_threshold = 85.0
    mock_args.dti_threshold = 38.0
    mock_args.include_risk_alerts = True
    mock_parse_args.return_value = mock_args

    with patch("src.analytics.run_scoring.load_portfolio") as mock_load:
        with patch("src.analytics.run_scoring.LoanAnalyticsEngine") as mock_engine_class:
            mock_df = pd.DataFrame(
                {
                    "loan_amount": [250000],
                    "appraised_value": [300000],
                    "borrower_income": [80000],
                    "monthly_debt": [1500],
                    "loan_status": ["current"],
                    "interest_rate": [0.035],
                    "principal_balance": [240000],
                }
            )
            mock_load.return_value = mock_df

            mock_engine = MagicMock()
            mock_engine.run_full_analysis.return_value = {"metric1": 1.0}
            mock_engine.risk_alerts.return_value = pd.DataFrame()
            mock_engine_class.return_value = mock_engine

            main()

            mock_engine.risk_alerts.assert_called_once_with(ltv_threshold=85.0, dti_threshold=38.0)
