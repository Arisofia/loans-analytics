"""Tests for the semantic layer — contracts, dimensions, resolver."""

from __future__ import annotations

from datetime import date
from decimal import Decimal


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
            metric_id="par_30",
            metric_name="PAR 30",
            value=Decimal("4.5"),
            unit=MetricUnit.PERCENTAGE,
            as_of_date=date.today(),
            source_mart="portfolio_mart",
            thresholds=ThresholdBand(warning=Decimal("3.0"), critical=Decimal("5.0")),
        )
        assert contract.metric_id == "par_30"
        assert contract.unit == MetricUnit.PERCENTAGE

    def test_is_breached(self):
        contract = MetricContract(
            metric_id="par_30",
            metric_name="PAR 30",
            value=Decimal("6.0"),
            unit=MetricUnit.PERCENTAGE,
            as_of_date=date.today(),
            source_mart="portfolio_mart",
            thresholds=ThresholdBand(warning=Decimal("3.0"), critical=Decimal("5.0")),
        )
        assert contract.is_breached()
        contract_low = MetricContract(
            metric_id="par_30",
            metric_name="PAR 30",
            value=Decimal("2.0"),
            unit=MetricUnit.PERCENTAGE,
            as_of_date=date.today(),
            source_mart="portfolio_mart",
            thresholds=ThresholdBand(warning=Decimal("3.0"), critical=Decimal("5.0")),
        )
        assert not contract_low.is_breached()

    def test_is_warning(self):
        contract = MetricContract(
            metric_id="par_30",
            metric_name="PAR 30",
            value=Decimal("4.0"),
            unit=MetricUnit.PERCENTAGE,
            as_of_date=date.today(),
            source_mart="portfolio_mart",
            thresholds=ThresholdBand(warning=Decimal("3.0"), critical=Decimal("5.0")),
        )
        assert contract.is_warning()
        contract_low = MetricContract(
            metric_id="par_30",
            metric_name="PAR 30",
            value=Decimal("2.0"),
            unit=MetricUnit.PERCENTAGE,
            as_of_date=date.today(),
            source_mart="portfolio_mart",
            thresholds=ThresholdBand(warning=Decimal("3.0"), critical=Decimal("5.0")),
        )
        assert not contract_low.is_warning()


class TestBusinessDimensions:
    def test_list_dimensions_non_empty(self):
        dims = list_dimensions()
        assert len(dims) >= 1  # at least some standard dims

    def test_get_dimension_by_id(self):
        dims = list_dimensions()
        if dims:
            dim = get_dimension(dims[0].dim_id)
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
        engine_output = {"par_30": 4.5, "collection_rate": 97.5}
        result = resolver.resolve_metric("par_30", engine_output)
        assert result is None or isinstance(result, MetricContract)

    def test_resolve_all(self):
        resolver = SemanticResolver()
        raw_metrics = {"par_30": 4.5, "collection_rate": 97.5}
        result = resolver.resolve_all(raw_metrics)
        assert isinstance(result, list)
