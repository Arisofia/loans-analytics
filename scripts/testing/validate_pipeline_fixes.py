from decimal import Decimal

import numpy as np
import pandas as pd

from src.pipeline.calculation import CalculationPhase
from src.pipeline.transformation import TransformationPhase


def test_pipeline_fixes():
    print("Starting validation test for pipeline fixes...")

    data = {
        "loan_id": ["LN-1", "LN-1", "LN-2"],
        "origination_date": ["2024-01-01", "2024-01-01", "2024-02-01"],
        "principal_amount": [1000.0, 1000.0, 5000.0],
        "outstanding_balance": [500.0, 500.0, 4000.0],
        "days_past_due": [0, 0, 95],
        "current_status": ["active", "active", "defaulted"],
        "country": ["El Salvador", "El Salvador", "El Salvador"],
        "Pledge Date": [np.nan, np.nan, np.nan],
        "Equifax Score": [700, -999, 650],
    }
    df_raw = pd.DataFrame(data)

    print("Testing Phase 2: Transformation...")
    transform = TransformationPhase(config={"null_handling": {"strategy": "smart"}})
    df_clean = transform._normalize_column_names(df_raw)

    assert "loan_uid" in df_clean.columns, "loan_uid was not generated"
    assert (
        df_clean["loan_uid"].nunique() == 2
    ), f"Expected 2 unique loans, found {df_clean['loan_uid'].nunique()}"
    print("  - loan_uid generation successful")

    conversions = {}
    transform._normalize_numeric_columns(df_clean, conversions)
    assert not pd.api.types.is_numeric_dtype(
        df_clean["country"]
    ), "country was incorrectly converted to numeric"
    print("  - country remains a string")

    transform._process_null_columns(df_clean, {"Pledge Date": 3}, 3)
    assert df_clean["Pledge Date"].isna().all(), "Pledge Date was incorrectly filled with 0"
    print("  - High-null columns preserved as NaN")

    print("Testing Phase 3: Calculation...")
    kpi_defs = {
        "portfolio_kpis": {
            "average_loan_size": {"formula": "AVG(amount)"},
            "total_loans_count": {"formula": "COUNT(loan_id)"},
        },
        "version": "3.0.0",
    }
    calc = CalculationPhase(config={}, kpi_definitions=kpi_defs)
    df_for_calc = df_clean.copy()
    results = calc._calculate_kpis(df_for_calc)

    avg_size = results.get("average_loan_size")
    assert avg_size == Decimal("3000.0"), f"Average loan size incorrect: {avg_size}"
    print(f"  - Average loan size: {avg_size} (Deduplication working)")

    assert "npl_90_ratio" in results, "npl_90_ratio missing"
    npl_ratio = float(results["npl_90_ratio"])
    # Total active balance = 500 + 500 + 4000 = 5000.
    # NPL balance (DPD > 90) = 4000. Ratio = 4000/5000 * 100 = 80.0%
    assert npl_ratio == 80.0, f"NPL ratio incorrect: {npl_ratio}"
    print(f"  - NPL 90 Ratio: {npl_ratio:.2f}% (Risk logic working)")

    print("\nALL VALIDATION TESTS PASSED!")


if __name__ == "__main__":
    test_pipeline_fixes()
