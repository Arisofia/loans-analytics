"""Tests for the semantic layer — contracts, dimensions, resolver."""

from __future__ import annotations

import pytest

from backend.src.semantic.metric_contracts import MetricUnit, MetricContract, ThresholdBand
from backend.src.semantic.business_dimensions import (
    Dimension,
    get_dimension,
    list_dimensions,
)
from backend.src.semantic.semantic_resolver import SemanticResolver


class TestMetricContract:
    def test_create_contract(self):
        contract = MetricContract(
            id="par_30",
            name="PAR 30",
            unit=MetricUnit.PERCENTAGE,
            warning=ThresholdBand(lower=3.0, upper=5.0),
            critical=ThresholdBand(lower=5.0, upper=100.0),
        )
        assert contract.id == "par_30"
        assert contract.unit == MetricUnit.PERCENTAGE

    def test_is_breached(self):
        contract = MetricContract(
            id="par_30",
            name="PAR 30",
            unit=MetricUnit.PERCENTAGE,
            warning=ThresholdBand(lower=3.0, upper=5.0),
            critical=ThresholdBand(lower=5.0, upper=100.0),
        )
        assert contract.is_breached(6.0)
        assert not contract.is_breached(2.0)

    def test_is_warning(self):
        contract = MetricContract(
            id="par_30",
            name="PAR 30",
            unit=MetricUnit.PERCENTAGE,
            warning=ThresholdBand(lower=3.0, upper=5.0),
            critical=ThresholdBand(lower=5.0, upper=100.0),
        )
        assert contract.is_warning(4.0)
        assert not contract.is_warning(2.0)


class TestBusinessDimensions:
    def test_list_dimensions_non_empty(self):
        dims = list_dimensions()
        assert len(dims) >= 1  # at least some standard dims

    def test_get_dimension_by_id(self):
        dims = list_dimensions()
        if dims:
            dim = get_dimension(dims[0].id)
            assert dim is not None
            assert isinstance(dim, Dimension)

    def test_get_unknown_dimension_returns_none(self):
        result = get_dimension("nonexistent_dimension_xyz")
        assert result is None


class TestSemanticResolver:
    def test_resolver_instantiates(self):
        resolver = SemanticResolver()
        assert resolver is not None

    def test_resolve_metric(self):
        resolver = SemanticResolver()
        # resolve_metric should accept a metric ID and raw value
        result = resolver.resolve_metric("par_30", 4.5)
        assert isinstance(result, dict)

    def test_resolve_all(self):
        resolver = SemanticResolver()
        raw_metrics = {"par_30": 4.5, "collection_rate": 97.5}
        result = resolver.resolve_all(raw_metrics)
        assert isinstance(result, dict)
