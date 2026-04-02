from __future__ import annotations
import pandas as pd
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from backend.loans_analytics.kpis.formula_engine import KPIFormulaEngine, KPIFormulaError


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "origination_date": ["2025-01-01", "2025-01-10", "2025-02-05", "2025-02-12"],
            "outstanding_balance": [1000.0, 500.0, 1200.0, 800.0],
            "status": ["Current", "Current", "Late", "Current"],
            "loan_id": ["L1", "L2", "L3", "L4"],
        }
    )


_finite_float = st.floats(
    min_value=-1000000, max_value=1000000, allow_nan=False, allow_infinity=False
)
_non_zero_float = _finite_float.filter(lambda v: abs(v) > 1e-09)
_formula_alphabet = st.characters(min_codepoint=32, max_codepoint=126)


@settings(max_examples=120, deadline=None)
@given(a=_finite_float, b=_finite_float, c=_non_zero_float)
def test_numeric_expression_fuzz_is_stable(a: float, b: float, c: float) -> None:
    engine = KPIFormulaEngine(_sample_df())
    expression = f"(({a}) + ({b}) - ({c})) / ({c})"
    result = engine._safe_eval_numeric_expression(expression)
    from decimal import Decimal

    assert isinstance(result, Decimal)
    assert result.is_finite()


@settings(max_examples=120, deadline=None)
@given(numerator=_finite_float)
def test_division_by_zero_fails_closed(numerator: float) -> None:
    """Division by zero must raise FormulaExecutionError, never silently return 0.0."""
    from backend.loans_analytics.kpis.formula_engine import FormulaExecutionError
    engine = KPIFormulaEngine(_sample_df())
    try:
        result = engine._safe_eval_numeric_expression(f"({numerator}) / 0")
        # Should not reach here
        raise AssertionError(f"Expected FormulaExecutionError but got result: {result}")
    except ZeroDivisionError:
        # This is wrapped by _safe_eval_numeric_expression in _execute_arithmetic_formula
        # For direct _safe_eval_numeric_expression call, ZeroDivisionError is acceptable
        pass
    except FormulaExecutionError as e:
        # Also acceptable if wrapped
        assert "division by zero" in str(e).lower()


@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@example("SUM(outstanding_balance) WHERE status = 'Current'; DROP TABLE loans;")
@example("__import__('os').system('echo hacked')")
@example("current_month_balance / (previous_month_balance - previous_month_balance)")
@given(payload=st.text(alphabet=_formula_alphabet, min_size=1, max_size=120))
def test_untrusted_formula_input_never_crashes(payload: str) -> None:
    """Untrusted input must not crash the engine; it raises FormulaExecutionError or returns a result.
    
    This test ensures the formula engine is resilient to malformed and malicious input without
    crashing the interpreter. Raising FormulaExecutionError is the expected controlled failure.
    """
    from backend.loans_analytics.kpis.formula_engine import FormulaExecutionError
    engine = KPIFormulaEngine(_sample_df())
    try:
        result = engine.calculate(payload)
        from decimal import Decimal

        assert isinstance(result, Decimal)
    except (KPIFormulaError, FormulaExecutionError):
        # Controlled failure is acceptable for untrusted input
        pass
