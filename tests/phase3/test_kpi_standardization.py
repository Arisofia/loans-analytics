import pytest
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().rounding = ROUND_HALF_UP  # Must be before ssot import


def test_par30_boundary_rounding():
    """PAR30 at exact 5.0005 must round to 5.001, not 5.000."""
    from backend.loans_analytics.kpis.ssot_asset_quality import calculate_par

    result = calculate_par(
        balances_at_risk=Decimal("500050"),
        total_portfolio=Decimal("10000000"),
        dpd_threshold=30,
    )
    assert result == Decimal("5.001"), f"Expected 5.001, got {result}"


def test_lgd_empirical_floor_enforcement():
    from backend.src.kpi_engine.risk import compute_lgd

    # Even if recovery is 70%, LGD floor is 0.40
    result = compute_lgd(
        total_disbursed=Decimal("1000000"),
        total_recovered=Decimal("700000"),  # 70% recovery → LGD = 0.30 raw
        method="empirical",
        fixed_rate=Decimal("0.90"),
    )
    assert result == Decimal("0.4000"), f"LGD floor violated: {result}"


def test_lgd_empirical_ceil_enforcement():
    from backend.src.kpi_engine.risk import compute_lgd

    result = compute_lgd(
        total_disbursed=Decimal("1000000"),
        total_recovered=Decimal("0"),  # 0% recovery → LGD = 1.0 raw
        method="empirical",
        fixed_rate=Decimal("0.90"),
    )
    assert result == Decimal("0.9500"), f"LGD ceil violated: {result}"


def test_nim_uses_parameterized_funding_cost(tmp_path, monkeypatch):
    """NIM formula must read funding_cost_rate from config, not hardcode 0.08."""
    import yaml
    import os

    params = {"financial_assumptions": {"funding_cost_rate": 0.10}}
    cfg_path = tmp_path / "business_parameters.yml"
    cfg_path.write_text(yaml.dump(params))
    monkeypatch.setenv("BUSINESS_PARAMS_PATH", str(cfg_path))

    from backend.src.kpi_engine.revenue import compute_nim_proxy

    result = compute_nim_proxy(
        avg_interest_rate=Decimal("0.18"), config_path=str(cfg_path)
    )
    # With funding cost 10%, NIM = (0.18 - 0.10) * 100 = 8.00
    assert result == Decimal("8.00"), f"NIM with funding_cost=0.10 expected 8.00, got {result}"


def test_hhi_formula_correctness():
    """HHI = Σ(share_i²) × 10000. Monopoly = 10000. Equal market = low."""
    from backend.src.kpi_engine.concentration import calculate_hhi

    # Two equal obligors: share = 0.5 each. HHI = 2 * (0.5²) * 10000 = 5000
    balances = [Decimal("500000"), Decimal("500000")]
    hhi = calculate_hhi(balances)
    assert hhi == Decimal("5000"), f"Expected HHI 5000, got {hhi}"

    # Monopoly: one obligor takes 100%
    monopoly = calculate_hhi([Decimal("1000000")])
    assert monopoly == Decimal("10000"), f"Monopoly HHI must be 10000, got {monopoly}"


def test_npl_definition_basel_aligned():
    """NPL must include DPD>=90 OR status=defaulted. Not DPD>=90 alone."""
    from backend.loans_analytics.kpis.ssot_asset_quality import calculate_npl
    import pandas as pd

    df = pd.DataFrame(
        {
            "balance": [100_000, 200_000, 50_000, 75_000],
            "dpd": [0, 91, 30, 0],
            "status": ["active", "active", "active", "defaulted"],
        }
    )
    # Loans 1 (DPD 91) and 3 (status=defaulted) should be in NPL
    # NPL balance = 200_000 + 75_000 = 275_000
    # Total       = 100_000 + 200_000 + 50_000 + 75_000 = 425_000
    # NPL%        = 275_000 / 425_000 * 100 = 64.71%
    result = calculate_npl(df, balance_col="balance", dpd_col="dpd", status_col="status")
    expected = Decimal("64.71")
    assert abs(result - expected) < Decimal("0.01"), f"NPL={result}, expected~{expected}"
