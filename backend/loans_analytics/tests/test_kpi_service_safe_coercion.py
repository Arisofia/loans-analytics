from decimal import ROUND_HALF_UP, getcontext
from typing import Any, cast

import pytest

getcontext().rounding = ROUND_HALF_UP


def _kpi_service_type():
    from backend.loans_analytics.apps.analytics.api.service import KPIService

    return KPIService


class _BadFloatRuntime:

    def __float__(self) -> float:
        return 1.0 / 0  # raises ZeroDivisionError — not caught by _safe_float/_safe_int


class _BadFloatValue:

    def __float__(self) -> float:
        raise TypeError("invalid number")


def test_safe_float_returns_zero_on_value_error() -> None:
    kpi_service = _kpi_service_type()
    assert kpi_service._safe_float(cast(Any, _BadFloatValue())) == 0.0


def test_safe_int_returns_default_on_value_error() -> None:
    kpi_service = _kpi_service_type()
    assert kpi_service._safe_int(cast(Any, _BadFloatValue()), default=3) == 3


def test_safe_float_propagates_unexpected_errors() -> None:
    kpi_service = _kpi_service_type()
    with pytest.raises(ZeroDivisionError):
        kpi_service._safe_float(cast(Any, _BadFloatRuntime()))


def test_safe_int_propagates_unexpected_errors() -> None:
    kpi_service = _kpi_service_type()
    with pytest.raises(ZeroDivisionError):
        kpi_service._safe_int(cast(Any, _BadFloatRuntime()))
