import pandas as pd

from src.kpis.aum import calculate_aum
from src.kpis.par_90 import calculate_par_90
from src.kpis.growth import calculate_growth


def make_df(balances, statuses=None, dpd_90=None, total_receivable=None):
    data = {"outstanding_loan_value": balances}
    if statuses is not None:
        data["loan_status"] = statuses
    if dpd_90 is not None:
        data["dpd_90_plus_usd"] = dpd_90
    if total_receivable is not None:
        data["total_receivable_usd"] = total_receivable
    return pd.DataFrame(data)


def test_par_and_aum_growth_integration():
    # Previous month: 3 current loans totaling 100
    df_prev = make_df([30.0, 30.0, 40.0], statuses=["current", "current", "current"], dpd_90=[0, 0, 0], total_receivable=[30, 30, 40])
    prev_aum, _ = calculate_aum(df_prev)

    # Current month: one loan went late >90 with 10 balance
    df_curr = make_df([25.0, 30.0, 35.0], statuses=["current", "current", "current"], dpd_90=[0, 0, 5], total_receivable=[25, 30, 35])
    curr_aum, _ = calculate_aum(df_curr)

    # Compute growth
    pct, ctx = calculate_growth(curr_aum, prev_aum)

    # Validate AUM numbers and growth
    assert prev_aum == 100.0
    assert curr_aum == 90.0
    assert pct == pytest.approx(-10.0)

    # PAR90 calculation (total dpd / total receivable)
    par, _ = calculate_par_90(df_curr)
    # dpd sum = 5, total receivable = 90 -> 5/90*100 = 5.555...
    assert par == pytest.approx((5 / 90) * 100, rel=1e-3)
