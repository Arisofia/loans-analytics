import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

from apps.analytics.src.enterprise_analytics_engine import LoanAnalyticsEngine


def test_engine_from_dict():
    from apps.analytics.tests.test_data_shared import SAMPLE_LOAN_DATA
    engine = LoanAnalyticsEngine.from_dict(SAMPLE_LOAN_DATA)
    assert isinstance(engine, LoanAnalyticsEngine)
    assert len(engine.loan_data) == 1


def test_engine_coercion_report_tracking():
    data = {
        "loan_amount": [250000, "invalid"],
        "appraised_value": [300000, 400000],
        "borrower_income": [80000, 90000],
        "monthly_debt": [1500, 2000],
        "loan_status": ["current", "current"],
        "interest_rate": [0.035, 0.04],
        "principal_balance": [240000, 390000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    # Prefer public API for test validation
    coercion_report = getattr(engine, '_coercion_report', None)
    assert coercion_report is not None
    assert coercion_report["loan_amount"] == 1


def test_engine_empty_dataframe():
    with pytest.raises(ValueError, match="non-empty pandas DataFrame"):
        LoanAnalyticsEngine(pd.DataFrame())


def test_engine_non_dataframe_input():
    with pytest.raises(ValueError, match="non-empty pandas DataFrame"):
        LoanAnalyticsEngine([1, 2, 3])


def test_engine_ltv_with_infinity():
    data = {
        "loan_amount": [250000, 450000],
        "appraised_value": [0, 500000],
        "borrower_income": [80000, 120000],
        "monthly_debt": [1500, 2500],
        "loan_status": ["current", "current"],
        "interest_rate": [0.035, 0.042],
        "principal_balance": [240000, 440000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    ltv = engine.compute_loan_to_value()
    assert not np.isinf(ltv).any()


def test_engine_dti_with_negative_income():
    data = {
        "loan_amount": [250000, 450000],
        "appraised_value": [300000, 500000],
        "borrower_income": [-80000, 120000],
        "monthly_debt": [1500, 2500],
        "loan_status": ["current", "current"],
        "interest_rate": [0.035, 0.042],
        "principal_balance": [240000, 440000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    dti = engine.compute_debt_to_income()
    assert dti.isna().iloc[0]


def test_engine_data_quality_with_duplicates():
    data = {
        "loan_amount": [250000, 250000, 150000],
        "appraised_value": [300000, 300000, 160000],
        "borrower_income": [80000, 80000, 60000],
        "monthly_debt": [1500, 1500, 1000],
        "loan_status": ["current", "current", "current"],
        "interest_rate": [0.035, 0.035, 0.038],
        "principal_balance": [240000, 240000, 145000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    quality = engine.data_quality_profile()
    assert quality["duplicate_ratio"] > 0


def test_engine_data_quality_with_null_values():
    data = {
        "loan_amount": [250000, None, 150000],
        "appraised_value": [300000, 500000, None],
        "borrower_income": [80000, 120000, 60000],
        "monthly_debt": [1500, 2500, 1000],
        "loan_status": ["current", "current", "current"],
        "interest_rate": [0.035, 0.042, 0.038],
        "principal_balance": [240000, 440000, 145000]
    }
    df = pd.DataFrame(data)
    engine = LoanAnalyticsEngine(df)
    quality = engine.data_quality_profile()
    assert quality["average_null_ratio"] > 0


def test_engine_data_quality_score_calculation():
    data = {
        "loan_amount": [250000, 450000, 150000],
        "appraised_value": [300000, 500000, 160000],
        "borrower_income": [80000, 120000, 60000],
        "monthly_debt": [1500, 2500, 1000],
        "loan_status": ["current", "current", "current"],
        "interest_rate": [0.035, 0.042, 0.038],
        "principal_balance": [240000, 440000, 145000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    quality = engine.data_quality_profile()
    assert 0 <= quality["data_quality_score"] <= 100


def test_engine_risk_alerts_empty_result():
    data = {
        "loan_amount": [250000, 450000, 150000],
        "appraised_value": [300000, 500000, 160000],
        "borrower_income": [80000, 120000, 60000],
        "monthly_debt": [1500, 2500, 1000],
        "loan_status": ["current", "current", "current"],
        "interest_rate": [0.035, 0.042, 0.038],
        "principal_balance": [240000, 440000, 145000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    alerts = engine.risk_alerts(ltv_threshold=100.0, dti_threshold=100.0)
    assert alerts.empty


def test_engine_risk_alerts_risk_score_calculation():
    data = {
        "loan_amount": [300000],
        "appraised_value": [300000],
        "borrower_income": [60000],
        "monthly_debt": [3000],
        "loan_status": ["current"],
        "interest_rate": [0.035],
        "principal_balance": [290000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    alerts = engine.risk_alerts(ltv_threshold=90.0, dti_threshold=40.0)
    
    if not alerts.empty:
        assert "risk_score" in alerts.columns
        assert 0 <= alerts["risk_score"].iloc[0] <= 1


def test_engine_risk_alerts_with_nan_values():
    data = {
        "loan_amount": [300000, 400000],
        "appraised_value": [300000, 400000],
        "borrower_income": [0, 80000],
        "monthly_debt": [3000, 1500],
        "loan_status": ["current", "current"],
        "interest_rate": [0.035, 0.035],
        "principal_balance": [290000, 390000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    alerts = engine.risk_alerts()
    
    if not alerts.empty:
        assert not np.isnan(alerts["risk_score"]).any()


def test_engine_export_kpis_to_blob_invalid_blob_name():
    data = {
        "loan_amount": [250000],
        "appraised_value": [300000],
        "borrower_income": [80000],
        "monthly_debt": [1500],
        "loan_status": ["current"],
        "interest_rate": [0.035],
        "principal_balance": [240000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    mock_exporter = MagicMock()
    
    with pytest.raises(ValueError, match="blob_name must be a string"):
        engine.export_kpis_to_blob(mock_exporter, blob_name=123)


def test_engine_export_kpis_to_blob_valid():
    data = {
        "loan_amount": [250000],
        "appraised_value": [300000],
        "borrower_income": [80000],
        "monthly_debt": [1500],
        "loan_status": ["current"],
        "interest_rate": [0.035],
        "principal_balance": [240000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    mock_exporter = MagicMock()
    mock_exporter.upload_metrics.return_value = "container/blob.json"
    
    result = engine.export_kpis_to_blob(mock_exporter, blob_name="test.json")
    
    assert result == "container/blob.json"
    mock_exporter.upload_metrics.assert_called_once()


def test_engine_source_df_not_modified():
    data = {
        "loan_amount": [250000, 450000],
        "appraised_value": [300000, 500000],
        "borrower_income": [80000, 120000],
        "monthly_debt": [1500, 2500],
        "loan_status": ["current", "current"],
        "interest_rate": [0.035, 0.042],
        "principal_balance": [240000, 440000]
    }
    original_df = pd.DataFrame(data)
    original_values = original_df.copy()
    
    engine = LoanAnalyticsEngine(original_df)
    engine.run_full_analysis()
    
    pd.testing.assert_frame_equal(original_df, original_values)


def test_engine_coercion_preserves_all_nan_columns():
    data = {
        "loan_amount": [250000],
        "appraised_value": [300000],
        "borrower_income": [80000],
        "monthly_debt": [1500],
        "loan_status": ["current"],
        "interest_rate": ["invalid"],
        "principal_balance": [240000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    assert engine.coercion_report["interest_rate"] == 1
    assert pd.isna(engine.loan_data["interest_rate"].iloc[0])


def test_engine_run_full_analysis_returns_all_keys():
    data = {
        "loan_amount": [250000, 450000],
        "appraised_value": [300000, 500000],
        "borrower_income": [80000, 120000],
        "monthly_debt": [1500, 2500],
        "loan_status": ["current", "30-59 days past due"],
        "interest_rate": [0.035, 0.042],
        "principal_balance": [240000, 440000]
    }
    engine = LoanAnalyticsEngine(pd.DataFrame(data))
    kpis = engine.run_full_analysis()
    
    expected_keys = [
        "portfolio_delinquency_rate_percent",
        "portfolio_yield_percent",
        "average_ltv_ratio_percent",
        "average_dti_ratio_percent",
        "data_quality_score",
        "average_null_ratio_percent",
        "invalid_numeric_ratio_percent"
    ]
    
    for key in expected_keys:
        assert key in kpis


def test_engine_handles_all_nan_numeric_columns():
    data = {
        "loan_amount": [None, None],
        "appraised_value": [300000, 500000],
        "borrower_income": [80000, 120000],
        "monthly_debt": [1500, 2500],
        "loan_status": ["current", "current"],
        "interest_rate": [0.035, 0.042],
        "principal_balance": [240000, 440000]
    }
    df = pd.DataFrame(data)
    engine = LoanAnalyticsEngine(df)
    kpis = engine.run_full_analysis()
    assert isinstance(kpis, dict)
