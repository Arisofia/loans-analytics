"""Unit tests for SSOT extensions in KPIFormulaEngine."""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

from backend.python.kpis.formula.auditor import KPIFormulaAuditor
from backend.python.kpis.formula.parser import FormulaParser
from backend.python.kpis.formula.registry import KPIRegistry
from backend.python.kpis.formula_engine import KPIFormulaEngine, KPIFormulaError


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "loan_id": ["L1", "L2", "L3"],
            "outstanding_balance": [1000, 500, 1500],
            "dpd": [0, 45, 95],
            "status": ["active", "delinquent", "defaulted"],
        }
    )


def _registry_data() -> dict:
    return {
        "version": "3.1.0",
        "asset_quality_kpis": {
            "par_30": {
                "formula": "SUM(outstanding_balance WHERE dpd >= 30) / SUM(outstanding_balance) * 100",
                "unit": "percentage",
            },
            "zero_division_kpi": {
                "formula": "SUM(outstanding_balance WHERE dpd >= 200) / SUM(outstanding_balance WHERE dpd >= 200) * 100",
                "unit": "percentage",
            },
        },
    }


def test_calculate_kpi_returns_ssot_metadata() -> None:
    engine = KPIFormulaEngine(_sample_df(), actor="unit-test", run_id="run-123", registry_data=_registry_data())

    result = engine.calculate_kpi("par_30")

    assert result["kpi_name"] == "par_30"
    assert result["unit"] == "percentage"
    assert result["formula_version"] == "3.1.0"
    assert result["actor"] == "unit-test"
    assert result["run_id"] == "run-123"
    assert result["data_rows"] == 3
    assert isinstance(result["value"], Decimal)
    assert result["value"] == Decimal("66.66666700")


def test_calculate_kpi_records_audit_entry() -> None:
    engine = KPIFormulaEngine(_sample_df(), actor="qa", run_id="audit-1", registry_data=_registry_data())

    _ = engine.calculate_kpi("par_30")
    records = engine.get_audit_records()

    assert len(records) == 1
    assert records[0]["kpi_name"] == "par_30"
    assert records[0]["formula_version"] == "3.1.0"
    assert records[0]["actor"] == "qa"
    assert records[0]["run_id"] == "audit-1"


def test_calculate_kpi_missing_definition_raises() -> None:
    engine = KPIFormulaEngine(_sample_df(), registry_data=_registry_data())

    with pytest.raises(KPIFormulaError, match="not found in registry"):
        engine.calculate_kpi("unknown_kpi")


def test_division_by_zero_fails_closed() -> None:
    engine = KPIFormulaEngine(_sample_df(), registry_data=_registry_data())

    result = engine.calculate_kpi("zero_division_kpi")

    assert result["value"] == Decimal("0.0")


def test_parser_stub_classifies_formula() -> None:
    parser = FormulaParser()

    parsed = parser.parse("SUM(outstanding_balance) / SUM(principal_amount)")

    assert parsed.is_arithmetic is True
    assert parsed.is_comparison is False


def test_registry_loader_stub(tmp_path) -> None:
    registry_path = tmp_path / "kpis.yaml"
    registry_path.write_text(
        """
version: "1.0"
asset_quality_kpis:
  par_30:
    formula: "SUM(outstanding_balance)"
    unit: "USD"
""".strip(),
        encoding="utf-8",
    )

    registry = KPIRegistry(registry_path)

    assert registry.version() == "1.0"
    assert registry.get("par_30")["unit"] == "USD"


def test_auditor_stub_stores_entries() -> None:
    auditor = KPIFormulaAuditor()

    auditor.record({"kpi_name": "par_30", "result": "3.5"})

    records = auditor.all_records()
    assert len(records) == 1
    assert records[0]["kpi_name"] == "par_30"
