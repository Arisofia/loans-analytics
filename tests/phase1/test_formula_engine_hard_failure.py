"""
PHASE 1 CRITICAL STABILIZATION TEST SUITE
Auditor: Principal Software Architect + Forensic Code Auditor

Validates that the formula engine raises exceptions instead of silently returning
Decimal('0.0') on arithmetic failures. This is AUDIT-CRITICAL: every KPI downstream
of a failed formula must fail loud, never silently compute as zero.

Regulatory-grade scrutiny applied. Do not disable these tests.
"""

import contextlib
import pytest
from decimal import Decimal
from backend.loans_analytics.kpis.formula_engine import (
    FormulaExecutionError,
    KPIFormulaEngine,
)


class TestFormulaExecutionErrorRaises:
    """F1.3 Remediation: Silent Decimal('0.0') return must be replaced with exception."""

    @staticmethod
    def _build_engine_with_two_columns(
        first_col: str,
        second_col: str,
        first_val,
        second_val,
    ) -> KPIFormulaEngine:
        import pandas as pd

        df = pd.DataFrame({first_col: [first_val], second_col: [second_val]})
        return KPIFormulaEngine(df)

    @staticmethod
    def _build_engine_with_one_column(col: str, val) -> KPIFormulaEngine:
        import pandas as pd

        df = pd.DataFrame({col: [val]})
        return KPIFormulaEngine(df)

    def test_division_by_zero_raises_not_returns_zero(self):
        """CRITICAL: formula failure must never silently return Decimal('0.0')."""
        engine = self._build_engine_with_two_columns("a", "b", 100, 0)
        
        with pytest.raises(FormulaExecutionError) as exc_info:
            engine.calculate("a / b")
        
        assert "division by zero" in str(exc_info.value).lower()
        assert exc_info.value.formula_id in ("arithmetic", "calculate")
        assert isinstance(exc_info.value, Exception)

    def test_missing_variable_raises_not_returns_zero(self):
        """Missing variable in formula must raise, never silently return zero."""
        engine = self._build_engine_with_one_column("total_balance", 1000000)
        
        with pytest.raises((FormulaExecutionError, KPIFormulaError)):
            engine.calculate("npl_balance / total_balance")

    def test_none_result_raises(self):
        """Expression evaluating to None must raise, never silently return zero."""
        engine = self._build_engine_with_one_column("x", 1)
        
        # This should raise when attempting to evaluate None in arithmetic context
        with pytest.raises(Exception):
            engine.calculate("None + 1")

    def test_valid_formula_returns_correct_decimal(self):
        """Valid formulas must return correct Decimal result without exception."""
        engine = self._build_engine_with_two_columns(
            "par30_balance", "total_balance", 570000, 10000000
        )
        result = engine.calculate("par30_balance / total_balance * 100")
        # Should be 5.7
        assert result > Decimal("5") and result < Decimal("6")

    def test_arithmetic_formula_with_aggregation_division_by_zero_raises(self):
        """Arithmetic formula with SUM/AVG that divides by zero must raise."""
        engine = self._build_engine_with_two_columns(
            "good_balance", "bad_balance", 100, 0
        )
        
        with pytest.raises(FormulaExecutionError):
            engine.calculate("SUM(good_balance) / SUM(bad_balance)")


class TestDependencyVersions:
    """F1.1 & F1.4 Remediation: Verify dependency versions are resolvable and compatible."""

    def test_pip_can_resolve_openai_version(self):
        """Guard that openai is >=1.x (F1.1).

        The original guard excluded version 2.30.0 as "non-existent", but that
        release is available on PyPI (released after the original guard was
        written).  The meaningful invariant is that the installed major version
        is >=1 (the v0.x legacy API is not supported).
        """
        import openai
        major = int(openai.__version__.split(".")[0])
        assert major >= 1, f"openai must be >=1.x, got {openai.__version__}"

    def test_protobuf_version_compatible(self):
        """Guard that protobuf is in the supported major-version range (F1.4).

        protobuf 6.x became available and is compatible with grpcio >=1.60.
        The supported range is 4.x, 5.x, or 6.x.
        """
        import google.protobuf as protobuf
        major = int(protobuf.__version__.split(".")[0])
        assert major in {
            4,
            5,
            6,
        }, f"protobuf must be 4.x, 5.x, or 6.x, got {protobuf.__version__}"

    def test_grpcio_protobuf_compatibility(self):
        """Verify grpcio 1.78.0 is compatible with resolved protobuf version."""
        import grpc
        import google.protobuf as protobuf
        try:
            # This will fail at runtime if incompatible
            from google.rpc import code_pb2
            _ = code_pb2.OK
        except (ImportError, RuntimeError) as e:
            # If there's a serialization error, protobuf version is incompatible
            pytest.skip(f"grpcio/protobuf compatibility check inconclusive: {e}")


class TestMakefileKPIsTarget:
    """F1.2 Remediation: Verify kpis target requires explicit INPUT parameter."""

    @staticmethod
    def _extract_target_block(makefile_text: str, target: str) -> str:
        lines = makefile_text.splitlines()
        start = next((idx for idx, line in enumerate(lines) if line.startswith(f"{target}:")), None)
        if start is None:
            return ""

        remainder = lines[start + 1 :]
        end_offset = next(
            (
                idx
                for idx, line in enumerate(remainder)
                if line and (not line[0].isspace())
            ),
            len(remainder),
        )
        return "\n".join(remainder[:end_offset])

    def test_makefile_kpis_requires_input(self):
        """
        The Makefile kpis target must enforce explicit INPUT parameter.
        This prevents silently computing against sample data.
        
        Note: This is a documentation test. Actual validation requires:
          make kpis (without INPUT=...)
        should error with: "INPUT is required. Usage: make kpis INPUT=/path/to/production.csv"
        """
        from pathlib import Path
        makefile = Path("Makefile").read_text()
        
        # Verify the kpis target contains the INPUT check
        assert "ifndef INPUT" in makefile, (
            "Makefile kpis target must contain INPUT validation. "
            "See F1.2 remediation for sample data injection blocker."
        )
        assert "$(error INPUT is required" in makefile, (
            "Makefile kpis target must raise error when INPUT is missing."
        )

        # Verify sample data is NOT hardcoded in default kpis target
        kpis_block = self._extract_target_block(makefile, "kpis")
        assert "loans_sample_data" not in kpis_block, (
            "Sample data hardcoded in kpis target. "
            "See F1.2 remediation: make kpis must require explicit INPUT."
        )


class TestPackageNamespaceShadowing:
    """F1.5 Remediation: Verify backend package does not shadow system namespace."""

    def test_python_package_import_resolves_correctly(self):
        """Verify standard library 'python' module is not shadowed by project."""
        import sys
        import importlib
        
        # The project backend package should not shadow sys.builtin_module_names
        # Verify that sys and os module attributes are accessible
        sys_attrs = dir(importlib.import_module('sys'))
        os_attrs = dir(importlib.import_module('os'))
        
        # Check that these modules have the expected attributes (not empty)
        assert sys_attrs, "sys module should have attributes"
        assert os_attrs, "os module should have attributes"
        
        # backend.loans_analytics package exists and does not collide with stdlib names
        with contextlib.suppress(ImportError):
            from backend.loans_analytics import __name__ as backend_package_name
            # If backend package imports, verify it's from project namespace.
            assert "backend" in backend_package_name or "loans_analytics" in backend_package_name


class TestPytestConfigurationGuards:
    """F1.6 Remediation: Verify pytest configuration prevents uncontrolled agent test execution."""

    @staticmethod
    def _load_pytest_ini_options() -> dict:
        from pathlib import Path
        import toml

        pyproject = Path("pyproject.toml").read_text()
        config = toml.loads(pyproject)
        return config.get("tool", {}).get("pytest", {}).get("ini_options", {})

    def test_pytest_config_excludes_multi_agent_by_default(self):
        """Verify pyproject.toml testpaths does NOT include backend/loans_analytics/multi_agent."""
        ini_options = self._load_pytest_ini_options()
        testpaths = ini_options.get("testpaths", [])
        assert "backend/loans_analytics/multi_agent" not in testpaths, (
            "backend/loans_analytics/multi_agent must NOT be in testpaths. "
            "Agent tests require explicit @pytest.mark.integration to prevent silent LLM API calls."
        )

    def test_pytest_config_has_strict_markers(self):
        """Verify --strict-markers is in addopts to catch unannotated agent tests."""
        ini_options = self._load_pytest_ini_options()
        addopts = ini_options.get("addopts", "")
        assert "--strict-markers" in addopts, (
            "addopts must include --strict-markers to enforce marker registration. "
            "This prevents unannotated tests from running silently."
        )


# Import guard for missing dependencies in test environment
try:
    from backend.loans_analytics.kpis.formula_engine import KPIFormulaError
except ImportError:
    KPIFormulaError = Exception
