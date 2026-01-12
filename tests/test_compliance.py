import pandas as pd

from src.compliance import (
    build_compliance_report,
    create_access_log_entry,
    mask_pii_in_dataframe,
)


def test_mask_pii_columns_by_keywords():
    df = pd.DataFrame({"borrower_name": ["Alice"], "loan_amount": [100.0]})
    masked_df, columns = mask_pii_in_dataframe(df)
    assert "borrower_name" in columns
    assert masked_df["borrower_name"].iloc[0].startswith("MASKED:")
    assert masked_df["loan_amount"].iloc[0] == 100.0


def test_mask_pii_columns_override():
    df = pd.DataFrame({"customer_id": ["ABC123"], "loan_amount": [200.0]})
    masked_df, columns = mask_pii_in_dataframe(df, pii_columns=["customer_id"])
    assert columns == ["customer_id"]
    assert masked_df["customer_id"].iloc[0].startswith("MASKED:")
    assert masked_df["loan_amount"].iloc[0] == 200.0


def test_access_log_entry_contains_context():
    entry = create_access_log_entry("stage", "user42", "manual", "completed", "done")
    assert entry["stage"] == "stage"
    assert entry["user"] == "user42"
    assert entry["status"] == "completed"
    assert entry.get("message") == "done"
    assert entry.get("timestamp") is not None


def test_build_compliance_report_includes_metadata():
    report = build_compliance_report("run123", [], [], "none", {"user": "u"})
    assert report["run_id"] == "run123"
    assert report["mask_stage"] == "none"
    assert report["metadata"]["user"] == "u"
