"""Property-based security and stability tests for KPIFormulaEngine."""

from __future__ import annotations

import pandas as pd
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from src.pipeline.calculation import KPIFormulaEngine


def _sample_df() -> pd.DataFrame:
    """Representative portfolio slice for formula fuzzing."""
    return pd.DataFrame(
        {
            "origination_date": ["2025-01-01", "2025-01-10", "2025-02-05", "2025-02-12"],
            "outstanding_balance": [1000.0, 500.0, 1200.0, 800.0],
            "status": ["Current", "Current", "Late", "Current"],
            "loan_id": ["L1", "L2", "L3", "L4"],
        }
    )


_finite_float = st.floats(
    min_value=-1_000_000,
    max_value=1_000_000,
    allow_nan=False,
    allow_infinity=False,
)
_non_zero_float = _finite_float.filter(lambda v: abs(v) > 1e-9)
_formula_alphabet = st.characters(min_codepoint=32, max_codepoint=126)


@settings(max_examples=120, deadline=None)
@given(a=_finite_float, b=_finite_float, c=_non_zero_float)
def test_numeric_expression_fuzz_is_stable(a: float, b: float, c: float) -> None:
    """Arithmetic expression evaluation should stay finite for valid numeric inputs."""
    engine = KPIFormulaEngine(_sample_df())
    expression = f"(({a}) + ({b}) - ({c})) / ({c})"

    result = engine._safe_eval_numeric_expression(expression)  # noqa: SLF001

    from decimal import Decimal

    assert isinstance(result, Decimal)
    assert result.is_finite()


@settings(max_examples=120, deadline=None)
@given(numerator=_finite_float)
def test_division_by_zero_fails_closed(numerator: float) -> None:
    """Division-by-zero must return 0.0 instead of raising."""
    engine = KPIFormulaEngine(_sample_df())

    result = engine._safe_eval_numeric_expression(f"({numerator}) / 0")  # noqa: SLF001

    from decimal import Decimal

    assert result == Decimal("0.0")


@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@example("SUM(outstanding_balance) WHERE status = 'Current'; DROP TABLE loans;")
@example("__import__('os').system('echo hacked')")
@example("current_month_balance / (previous_month_balance - previous_month_balance)")
@given(payload=st.text(alphabet=_formula_alphabet, min_size=1, max_size=120))
def test_untrusted_formula_input_never_crashes(payload: str) -> None:
    """Engine must fail closed for arbitrary formula payloads."""
    engine = KPIFormulaEngine(_sample_df())

    result = engine.calculate(payload)

    from decimal import Decimal

    assert isinstance(result, Decimal)
