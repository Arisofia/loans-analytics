from typing import Any, cast
import pytest
from backend.python.apps.analytics.api.service import KPIService

class _BadFloatRuntime:

    def __float__(self) -> float:
        raise RuntimeError('conversion bug')

class _BadFloatValue:

    def __float__(self) -> float:
        raise ValueError('invalid number')

def test_safe_float_returns_default_on_value_error() -> None:
    assert KPIService._safe_float(cast(Any, _BadFloatValue()), default=7.5) == 0.0

def test_safe_int_returns_default_on_value_error() -> None:
    assert KPIService._safe_int(cast(Any, _BadFloatValue()), default=3) == 3

def test_safe_float_propagates_unexpected_runtime_errors() -> None:
    with pytest.raises(RuntimeError, match='conversion bug'):
        KPIService._safe_float(cast(Any, _BadFloatRuntime()))

def test_safe_int_propagates_unexpected_runtime_errors() -> None:
    with pytest.raises(RuntimeError, match='conversion bug'):
        KPIService._safe_int(cast(Any, _BadFloatRuntime()))
