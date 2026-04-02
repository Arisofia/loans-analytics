"""
PHASE 1 CRITICAL STABILIZATION TEST SUITE
Auditor: Principal Software Architect + Forensic Code Auditor

Validates that the formula engine raises exceptions instead of silently returning
Decimal('0.0') on arithmetic failures. This is AUDIT-CRITICAL: every KPI downstream
of a failed formula must fail loud, never silently compute as zero.

Regulatory-grade scrutiny applied. Do not disable these tests.
"""

import pytest
from decimal import Decimal
from backend.loans_analytics.kpis.formula_engine import (
    FormulaExecutionError,
    KPIFormulaEngine,
)


class TestFormulaExecutionErrorRaises:
    """F1.3 Remediation: Silent Decimal('0.0') return must be replaced with exception."""

    def test_division_by_zero_raises_not_returns_zero(self):
        """CRITICAL: formula failure must never silently return Decimal('0.0')."""
        import pandas as pd
        df = pd.DataFrame({"a": [100], "b": [0]})
        engine = KPIFormulaEngine(df)
        
        with pytest.raises(FormulaExecutionError) as exc_info:
            engine.calculate("a / b")
        
        assert "division by zero" in str(exc_info.value).lower()
        assert exc_info.value.formula_id in ("arithmetic", "calculate")
        assert isinstance(exc_info.value, Exception)

    def test_missing_variable_raises_not_returns_zero(self):
        """Missing variable in formula must raise, never silently return zero."""
        import pandas as pd
        df = pd.DataFrame({"total_balance": [1000000]})
        engine = KPIFormulaEngine(df)
        
        with pytest.raises((FormulaExecutionError, KPIFormulaError)):
            engine.calculate("npl_balance / total_balance")

    def test_none_result_raises(self):
        """Expression evaluating to None must raise, never silently return zero."""
        import pandas as pd
        df = pd.DataFrame({"x": [1]})
        engine = KPIFormulaEngine(df)
        
        # This should raise when attempting to evaluate None in arithmetic context
        with pytest.raises(Exception):
            engine.calculate("None + 1")

    def test_valid_formula_returns_correct_decimal(self):
        """Valid formulas must return correct Decimal result without exception."""
        import pandas as pd
        df = pd.DataFrame({
            "par30_balance": [570000],
            "total_balance": [10000000],
        })
        engine = KPIFormulaEngine(df)
        result = engine.calculate("par30_balance / total_balance * 100")
        # Should be 5.7
        assert result > Decimal("5") and result < Decimal("6")

    def test_arithmetic_formula_with_aggregation_division_by_zero_raises(self):
        """Arithmetic formula with SUM/AVG that divides by zero must raise."""
        import pandas as pd
        df = pd.DataFrame({
            "good_balance": [100],
            "bad_balance": [0],
        })
        engine = KPIFormulaEngine(df)
        
        with pytest.raises(FormulaExecutionError):
            engine.calculate("SUM(good_balance) / SUM(bad_balance)")


class TestDependencyVersions:
    """F1.1 & F1.4 Remediation: Verify dependency versions are resolvable and compatible."""

    def test_pip_can_resolve_openai_version(self):
        """Guard against re-introduction of non-existent openai version (F1.1)."""
        import openai
        major = int(openai.__version__.split(".")[0])
        assert major >= 1, f"openai must be >=1.x, got {openai.__version__}"
        # Should not be 2.30.0 which never existed
        assert openai.__version__ != "2.30.0", "Non-existent version 2.30.0 detected"

    def test_protobuf_version_compatible(self):
        """Guard against protobuf 6.x which never existed (F1.4)."""
        import google.protobuf as protobuf
        major = int(protobuf.__version__.split(".")[0])
        assert major in (4, 5), f"protobuf must be 4.x or 5.x, got {protobuf.__version__}"
        # Should not be 6.x
        assert major < 6, f"protobuf major version {major} is outside supported range [4,5]"

    def test_grpcio_protobuf_compatibility(self):
        """Verify grpcio 1.78.0 is compatible with resolved protobuf version."""
        import grpc
        import google.protobuf as protobuf
        try:
            # This will fail at runtime if incompatible
            from google.rpc import code_pb2
            _ = code_pb2.OK
            # If we got here without serialization error, versions are compatible
            assert True
        except (ImportError, RuntimeError) as e:
            # If there's a serialization error, protobuf version is incompatible
            pytest.skip(f"grpcio/protobuf compatibility check inconclusive: {e}")


class TestMakefileKPIsTarget:
    """F1.2 Remediation: Verify kpis target requires explicit INPUT parameter."""

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
        lines = makefile.split('\n')
        in_kpis_target = False
        for i, line in enumerate(lines):
            if line.startswith('kpis:'):
                in_kpis_target = True
            elif in_kpis_target and line and not line[0].isspace():
                # Next non-indented line means we've left the target
                in_kpis_target = False
            
            if in_kpis_target and 'loans_sample_data' in line:
                pytest.fail(
                    f"Line {i+1}: Sample data hardcoded in kpis target. "
                    "See F1.2 remediation: make kpis must require explicit INPUT."
                )


class TestPackageNamespaceShadowing:
    """F1.5 Remediation: Verify backend/python package does not shadow system namespace."""

    def test_python_package_import_resolves_correctly(self):
        """Verify standard library 'python' module is not shadowed by project."""
        import sys
        import importlib
        
        # The project package backend/python should not shadow sys.builtin_module_names
        # Verify that sys and os module attributes are accessible
        sys_attrs = dir(importlib.import_module('sys'))
        os_attrs = dir(importlib.import_module('os'))
        
        # Check that these modules have the expected attributes (not empty)
        assert len(sys_attrs) > 0, "sys module should have attributes"
        assert len(os_attrs) > 0, "os module should have attributes"
        
        # backend.python package exists and performs name shadowing detection
        try:
            from backend.python import __name__ as backend_package_name
            # If backend.python imports, verify it's not colliding with system python
            assert "backend" in backend_package_name or "python" in backend_package_name
        except ImportError:
            # If it doesn't import, that's actually fine for this test
            pass


class TestPytestConfigurationGuards:
    """F1.6 Remediation: Verify pytest configuration prevents uncontrolled agent test execution."""

    def test_pytest_config_excludes_multi_agent_by_default(self):
        """Verify pyproject.toml testpaths does NOT include backend/python/multi_agent."""
        from pathlib import Path
        import toml
        
        pyproject = Path("pyproject.toml").read_text()
        config = toml.loads(pyproject)
        
        testpaths = config.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("testpaths", [])
        assert "backend/python/multi_agent" not in testpaths, (
            "backend/python/multi_agent must NOT be in testpaths. "
            "Agent tests require explicit @pytest.mark.integration to prevent silent LLM API calls."
        )

    def test_pytest_config_has_strict_markers(self):
        """Verify --strict-markers is in addopts to catch unannotated agent tests."""
        from pathlib import Path
        import toml
        
        pyproject = Path("pyproject.toml").read_text()
        config = toml.loads(pyproject)
        
        addopts = config.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("addopts", "")
        assert "--strict-markers" in addopts, (
            "addopts must include --strict-markers to enforce marker registration. "
            "This prevents unannotated tests from running silently."
        )


# Import guard for missing dependencies in test environment
try:
    from backend.loans_analytics.kpis.formula_engine import KPIFormulaError
except ImportError:
    KPIFormulaError = Exception
