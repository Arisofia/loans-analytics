import pandas as pd
import pytest
from pipeline.validation import DataQualityReporter

def test_data_quality_report_passed():
    df = pd.DataFrame({
        "loan_id": ["1", "2"],
        "total_receivable_usd": [100.0, 200.0],
        "measurement_date": ["2026-01-01", "2026-01-02"]
    })
    
    reporter = DataQualityReporter(df)
    report = reporter.run_audit(
        required_columns=["loan_id", "total_receivable_usd"],
        numeric_columns=["total_receivable_usd"],
        date_columns=["measurement_date"]
    )
    
    assert report.status == "passed"
    assert report.score == 100.0
    assert "PASSED" in report.to_markdown()

def test_data_quality_report_failed_missing_column():
    df = pd.DataFrame({
        "loan_id": ["1", "2"]
    })
    
    reporter = DataQualityReporter(df)
    report = reporter.run_audit(
        required_columns=["loan_id", "total_receivable_usd"]
    )
    
    assert report.status == "failed"
    assert "total_receivable_usd" in report.missing_columns
    assert "🔴 FAILED" in report.to_markdown()

def test_data_quality_report_type_error():
    df = pd.DataFrame({
        "loan_id": ["1", "2"],
        "total_receivable_usd": ["not_a_number", "200.0"]
    })
    
    reporter = DataQualityReporter(df)
    report = reporter.run_audit(
        required_columns=["loan_id"],
        numeric_columns=["total_receivable_usd"]
    )
    
    assert report.score < 100.0
    assert any("non-numeric" in err for err in report.type_errors)
