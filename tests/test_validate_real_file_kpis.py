import pandas as pd
from pathlib import Path

from scripts.validation.validate_real_file_kpis import build_validation_report


def test_build_validation_report_flags_blanks_and_negatives():
    df = pd.DataFrame(
        {
            "outstanding_balance": [1000, -200, 0],
            "dpd": [10, 45, 95],
            "status": ["active", "delinquent", "defaulted"],
            "borrower_id": ["a", "", None],
        }
    )

    report = build_validation_report(df=df, source_path=Path("/tmp/sample.csv"))

    assert report["rows"] == 3
    assert report["negative_counts"]["outstanding_balance"] == 1
    assert report["blank_counts"]["borrower_id"] == 2
    assert report["core_kpis_from_real_file"]["par_30"] is not None
