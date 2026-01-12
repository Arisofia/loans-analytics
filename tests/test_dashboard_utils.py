import pandas as pd
from src.utils.dashboard_utils import compute_cat_agg


def test_compute_cat_agg_missing_value_col():
    df = pd.DataFrame({"categoria": ["A", "B"], "other_col": [1, 2]})
    res = compute_cat_agg(df)
    assert res.empty


def test_compute_cat_agg_with_values():
    df = pd.DataFrame({
        "categoria": ["A", "B", "A"],
        "outstanding_loan_value": [100, 0, 50],
    })
    res = compute_cat_agg(df)
    # Ensure categories are present and sums aggregated correctly
    a_val = res.loc[res["categoria"] == "A", "outstanding_loan_value"].values
    assert a_val.size == 1
    assert a_val[0] == 150
