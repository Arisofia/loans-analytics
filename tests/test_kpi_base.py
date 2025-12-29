import pytest
import pandas as pd
from python.kpis.base import safe_numeric, create_context, KPIMetadata


class TestSafeNumeric:
    def test_safe_numeric_valid(self):
        series = pd.Series([1.0, 2.0, 3.0])
        result = safe_numeric(series)
        assert result.sum() == 6.0

    def test_safe_numeric_with_nulls(self):
        series = pd.Series([1.0, None, 3.0])
        result = safe_numeric(series)
        assert result.sum() == 4.0

    def test_safe_numeric_with_custom_fill(self):
        series = pd.Series([1.0, None, 3.0])
        result = safe_numeric(series, fill_value=10.0)
        assert result[1] == 10.0

    def test_safe_numeric_coercion(self):
        series = pd.Series(["1.5", "2.5", "invalid"])
        result = safe_numeric(series)
        assert result[0] == 1.5
        assert result[1] == 2.5
        assert result[2] == 0.0


class TestCreateContext:
    def test_create_context_basic(self):
        ctx = create_context("test_formula", rows_processed=100)
        assert ctx["formula"] == "test_formula"
        assert ctx["rows_processed"] == 100
        assert "timestamp" in ctx

    def test_create_context_with_nulls(self):
        ctx = create_context("test", rows_processed=100, null_count=5)
        assert ctx["null_count"] == 5

    def test_create_context_with_extra(self):
        ctx = create_context("test", rows_processed=100, custom_field="value")
        assert ctx["custom_field"] == "value"


class TestKPIMetadata:
    def test_metadata_creation(self):
        metadata = KPIMetadata(
            name="PAR90",
            description="Test",
            formula="test_formula",
            unit="%",
            data_sources=["test_source"],
            threshold_warning=5.0,
            threshold_critical=10.0,
        )
        assert metadata.name == "PAR90"
        assert metadata.threshold_warning == 5.0

    def test_metadata_to_dict(self):
        metadata = KPIMetadata(
            name="PAR90",
            description="Test",
            formula="test_formula",
            unit="%",
            data_sources=["test_source"],
        )
        d = metadata.to_dict()
        assert d["name"] == "PAR90"
        assert "formula" in d
