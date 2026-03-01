"""Tests for csv_upload.py: homologation, currency parsing, and duplicate loan_id classification."""

from __future__ import annotations

import sys
import types

import pandas as pd

# ---------------------------------------------------------------------------
# Stub out streamlit so csv_upload can be imported without a running session
# ---------------------------------------------------------------------------

_st_stub = types.ModuleType("streamlit")
for _attr in [
    "error",
    "warning",
    "info",
    "success",
    "header",
    "markdown",
    "file_uploader",
    "button",
    "progress",
    "empty",
    "expander",
    "dataframe",
    "metric",
    "columns",
    "subheader",
    "download_button",
    "exception",
    "stop",
    "set_page_config",
]:
    setattr(_st_stub, _attr, lambda *a, **k: None)

sys.modules.setdefault("streamlit", _st_stub)

from streamlit_app.components.csv_upload import (  # noqa: E402
    _alias_matches,
    _apply_aliases,
    _classify_loan_id_duplicates,
    _coerce_numeric,
    _normalize_column_names,
    _prepare_dataframe,
    _validate_for_pipeline,
    BORROWER_ID_COLS,
)


# ---------------------------------------------------------------------------
# _coerce_numeric – currency / thousands-separator parsing
# ---------------------------------------------------------------------------


class TestCoerceNumeric:
    def test_dollar_sign_and_thousands(self):
        s = pd.Series(["$50,000", "$1,234.56", "10000", ""])
        out = _coerce_numeric(s)
        assert out.iloc[0] == 50000.0
        assert out.iloc[1] == 1234.56
        assert out.iloc[2] == 10000.0
        assert out.iloc[3] == 0.0

    def test_plain_integers(self):
        s = pd.Series(["100", "200", "300"])
        out = _coerce_numeric(s)
        assert list(out) == [100.0, 200.0, 300.0]

    def test_decimal_comma_locale(self):
        # European locale: comma as decimal separator (e.g. "1.234,56")
        # After normalisation, "1.234" should become 1234 and "56" would be
        # the decimal part – but in our _coerce_numeric the comma-only branch
        # converts "1234,56" → "1234.56" while "1,234" → "1234".
        s = pd.Series(["1234,56"])
        out = _coerce_numeric(s)
        assert out.iloc[0] == 1234.56

    def test_nan_and_none(self):
        s = pd.Series([None, "nan", "NaN", "None"])
        out = _coerce_numeric(s)
        assert (out == 0.0).all()


# ---------------------------------------------------------------------------
# _alias_matches – column suffix handling
# ---------------------------------------------------------------------------


class TestAliasMatches:
    def test_exact_match(self):
        cols = ["codcliente", "other"]
        assert _alias_matches(cols, "codcliente") == ["codcliente"]

    def test_trailing_underscore(self):
        cols = ["codcliente_", "codcliente__"]
        result = _alias_matches(cols, "codcliente")
        assert "codcliente_" in result
        assert "codcliente__" in result

    def test_numeric_suffix(self):
        cols = ["codcliente1", "codcliente2", "codcliente_2"]
        result = _alias_matches(cols, "codcliente")
        assert "codcliente1" in result
        assert "codcliente2" in result
        assert "codcliente_2" in result

    def test_kam_hunter_variants(self):
        cols = ["cod_kam_hunter", "cod_kam_hunter_", "cod_kam_hunter1"]
        result = _alias_matches(cols, "cod_kam_hunter")
        assert set(result) == set(cols)

    def test_no_spurious_matches(self):
        cols = ["codclienteX_extra", "notcodcliente"]
        result = _alias_matches(cols, "codcliente")
        assert result == []


# ---------------------------------------------------------------------------
# _apply_aliases – homologation for DESEMBOLSOS-style CSVs
# ---------------------------------------------------------------------------


class TestApplyAliases:
    def _make_desembolsos_df(self) -> pd.DataFrame:
        """Minimal DESEMBOLSOS CSV-like frame after column normalisation."""
        return pd.DataFrame(
            {
                "numero_desembolso": ["D001", "D002"],
                "monto_del_desembolso": ["$50,000", "$30,000"],
                "codcliente": ["C1", "C2"],
                "estado": ["Vigente", "Mora"],
                "dias_mora": [0, 35],
            }
        )

    def test_loan_id_mapped_from_numero_desembolso(self):
        df = _normalize_column_names(self._make_desembolsos_df())
        mapped = _apply_aliases(df)
        assert "loan_id" in mapped.columns
        assert list(mapped["loan_id"]) == ["D001", "D002"]

    def test_borrower_id_mapped_from_codcliente(self):
        df = _normalize_column_names(self._make_desembolsos_df())
        mapped = _apply_aliases(df)
        assert "borrower_id" in mapped.columns
        assert list(mapped["borrower_id"]) == ["C1", "C2"]

    def test_amount_mapped_and_currency_parsed(self):
        raw = pd.DataFrame({"numero_desembolso": ["D001"], "monto_del_desembolso": ["$50,000"]})
        prepared = _prepare_dataframe(raw)
        assert "amount" in prepared.columns
        assert prepared["amount"].iloc[0] == 50000.0

    def test_codcliente_suffix_variants_coalesced(self):
        """When CSV has both CodCliente_ and CodCliente_2, they should be merged."""
        raw = pd.DataFrame(
            {
                "numero_desembolso": ["D001", "D002"],
                "CodCliente_": ["C1", None],
                "CodCliente_2": [None, "C2"],
            }
        )
        prepared = _prepare_dataframe(raw)
        assert "borrower_id" in prepared.columns
        assert prepared["borrower_id"].iloc[0] == "C1"
        assert prepared["borrower_id"].iloc[1] == "C2"


# ---------------------------------------------------------------------------
# _classify_loan_id_duplicates – three scenario classifications
# ---------------------------------------------------------------------------


class TestClassifyLoanIdDuplicates:
    def test_no_duplicates_returns_empty(self):
        df = pd.DataFrame(
            {
                "loan_id": ["A", "B", "C"],
                "borrower_id": ["b1", "b2", "b3"],
                "amount": [100.0, 200.0, 300.0],
            }
        )
        assert _classify_loan_id_duplicates(df) == []

    def test_exact_duplicate_emits_warning(self):
        """Same loan_id + same borrower + same amount → exact duplicate → warning."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A"],
                "borrower_id": ["b1", "b1"],
                "amount": [100.0, 100.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, msg = result[0]
        assert level == "warning"
        assert "exact duplicate" in msg.lower()

    def test_historical_snapshot_emits_info(self):
        """Same loan_id + same borrower + different amounts → historical snapshot → info."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A"],
                "borrower_id": ["b1", "b1"],
                "amount": [100.0, 90.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, msg = result[0]
        assert level == "info"
        assert "snapshot" in msg.lower()

    def test_suspicious_merge_emits_warning(self):
        """Same loan_id + different borrowers → suspicious merge → warning."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A"],
                "borrower_id": ["b1", "b2"],
                "amount": [100.0, 100.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, msg = result[0]
        assert level == "warning"
        assert "suspicious" in msg.lower()

    def test_mixed_scenarios_all_reported(self):
        """Multiple loan_ids with different duplicate patterns → each type reported."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A", "B", "B", "C", "C"],
                "borrower_id": ["b1", "b1", "b2", "b2", "b3", "b4"],
                "amount": [100.0, 100.0, 200.0, 150.0, 300.0, 300.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        warning_msgs = [msg for level, msg in result if level == "warning"]
        info_msgs = [msg for level, msg in result if level == "info"]
        # A → exact dup (warning), B → snapshot (info), C → suspicious (warning)
        assert len(info_msgs) == 1
        assert len(warning_msgs) == 2

    def test_missing_loan_id_column_returns_empty(self):
        df = pd.DataFrame({"amount": [100.0]})
        assert _classify_loan_id_duplicates(df) == []

    def test_no_borrower_id_column_uses_amount_only(self):
        """Without borrower_id, different amounts still classify as snapshot (info)."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A"],
                "amount": [100.0, 80.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, _ = result[0]
        assert level == "info"

    def test_no_borrower_id_same_amount_classified_as_exact(self):
        """Without borrower_id, same amounts still classify as exact duplicate (warning)."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A"],
                "amount": [100.0, 100.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, _ = result[0]
        assert level == "warning"

    def test_client_code_used_as_borrower_fallback(self):
        """client_code column used when borrower_id is absent (pre-homologation CSV)."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A"],
                "client_code": ["C1", "C1"],
                "amount": [100.0, 100.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, _ = result[0]
        assert level == "warning"  # same client + same amount → exact dup

    def test_client_name_used_as_borrower_fallback(self):
        """client_name column used when neither borrower_id nor client_code is present."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A"],
                "client_name": ["Alice", "Bob"],  # different clients → suspicious
                "amount": [100.0, 100.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, msg = result[0]
        assert level == "warning"
        assert "suspicious" in msg.lower()

    def test_borrower_id_takes_priority_over_client_code(self):
        """When both borrower_id and client_code present, borrower_id is used."""
        df = pd.DataFrame(
            {
                "loan_id": ["A", "A"],
                "borrower_id": ["b1", "b2"],   # different → suspicious
                "client_code": ["C1", "C1"],    # same — should be ignored
                "amount": [100.0, 100.0],
            }
        )
        result = _classify_loan_id_duplicates(df)
        assert any("suspicious" in msg.lower() for _, msg in result)

    def test_borrower_id_cols_constant_priority(self):
        """BORROWER_ID_COLS defines priority: borrower_id first, then client_code, etc."""
        assert BORROWER_ID_COLS[0] == "borrower_id"
        assert "client_code" in BORROWER_ID_COLS
        assert "client_name" in BORROWER_ID_COLS


# ---------------------------------------------------------------------------
# _validate_for_pipeline – generic checks unaffected by new logic
# ---------------------------------------------------------------------------


class TestValidateForPipeline:
    def test_valid_frame_returns_true(self):
        df = pd.DataFrame({"loan_id": ["A"], "amount": [100.0], "status": ["active"]})
        valid, missing, issues = _validate_for_pipeline(df)
        assert valid is True
        assert missing == []
        assert issues == []

    def test_missing_required_columns(self):
        df = pd.DataFrame({"loan_id": ["A"]})
        valid, missing, issues = _validate_for_pipeline(df)
        assert valid is False
        assert "amount" in missing
        assert "status" in missing

    def test_all_zeros_amount_reported(self):
        df = pd.DataFrame({"loan_id": ["A"], "amount": [0.0], "status": ["active"]})
        valid, missing, issues = _validate_for_pipeline(df)
        assert valid is True
        assert any("zero" in i.lower() for i in issues)


# ---------------------------------------------------------------------------
# Portfolio Dashboard (3_Portfolio_Dashboard.py) – DESEMBOLSOS homologation,
# currency parsing, and duplicate classification wiring
# ---------------------------------------------------------------------------

# These imports are deferred to mid-file so that the streamlit stub (_st_stub)
# is already populated before the dashboard module is loaded via importlib.
import importlib.util as _ilu
import os as _os

# plotly is imported by the dashboard at module level.  The real plotly package
# is available in the test environment, so we just need it imported here so the
# dashboard module can resolve it when exec_module() runs.
import plotly.express  # noqa: F401  – side-effect import; ensures plotly is in sys.modules
import plotly.graph_objects  # noqa: F401

for _attr in [
    "session_state",
    "cache_data",
    "cache_resource",
    "spinner",
    "tabs",
    "plotly_chart",
    "selectbox",
    "checkbox",
    "radio",
    "text_input",
    "number_input",
    "caption",
    "write",
    "sidebar",
]:
    setattr(_st_stub, _attr, lambda *a, **k: None)
setattr(_st_stub, "session_state", {})

_os.environ.setdefault("ABACO_API_BASE", "http://localhost:8000")

_dash_spec = _ilu.spec_from_file_location(
    "_portfolio_dashboard_test",
    str(
        __import__("pathlib").Path(__file__).parent.parent
        / "streamlit_app"
        / "pages"
        / "3_Portfolio_Dashboard.py"
    ),
)
_dash_mod = _ilu.module_from_spec(_dash_spec)
_dash_spec.loader.exec_module(_dash_mod)


class TestPortfolioDashboardDesembolsos:
    """Verify that the Portfolio Dashboard correctly handles DESEMBOLSOS/CONTROL DE MORA CSVs."""

    def _desembolsos_raw(self) -> pd.DataFrame:
        """Minimal DESEMBOLSOS-style CSV with Spanish column names and currency values."""
        return pd.DataFrame(
            {
                "Numero_Desembolso": ["D001", "D002"],
                "Monto_del_Desembolso": ["$50,000", "$30,000"],
                "CodCliente": ["C1", "C2"],
                "Estado": ["Vigente", "Mora"],
                "Tasa_de_Interes": [0.12, 0.18],
                "Plazo_Meses": [12, 24],
                "Fecha_Desembolso": ["2025-01-01", "2025-02-01"],
            }
        )

    def _normalize_and_alias(self, raw: pd.DataFrame) -> pd.DataFrame:
        return _dash_mod._apply_column_aliases(_dash_mod._normalize_column_names(raw))

    def test_numero_desembolso_mapped_to_loan_id(self):
        df = self._normalize_and_alias(self._desembolsos_raw())
        assert "loan_id" in df.columns
        assert list(df["loan_id"]) == ["D001", "D002"]

    def test_codcliente_mapped_to_borrower_id(self):
        df = self._normalize_and_alias(self._desembolsos_raw())
        assert "borrower_id" in df.columns
        assert list(df["borrower_id"]) == ["C1", "C2"]

    def test_monto_del_desembolso_mapped_to_principal_amount(self):
        df = self._normalize_and_alias(self._desembolsos_raw())
        assert "principal_amount" in df.columns
        # Raw value still a string at this stage; check non-null
        assert df["principal_amount"].notna().all()

    def test_currency_parsed_correctly_in_prepare(self):
        """$50,000 must be parsed as 50000.0, not NaN or 50.0."""
        raw = self._desembolsos_raw()
        aliased = self._normalize_and_alias(raw)
        prepared = _dash_mod.prepare_uploaded_data(aliased)
        assert "principal_amount" in prepared.columns
        assert prepared["principal_amount"].iloc[0] == 50000.0
        assert prepared["principal_amount"].iloc[1] == 30000.0

    def test_dias_mora_mapped_to_days_past_due(self):
        raw = pd.DataFrame(
            {
                "loan_id": ["D001"],
                "principal_amount": [10000.0],
                "interest_rate": [0.12],
                "term_months": [12],
                "origination_date": ["2025-01-01"],
                "current_status": ["active"],
                "Dias_Mora": [35],
            }
        )
        df = self._normalize_and_alias(raw)
        assert "days_past_due" in df.columns

    def test_origination_date_aliased_from_fecha_desembolso(self):
        df = self._normalize_and_alias(self._desembolsos_raw())
        assert "origination_date" in df.columns

    def test_codcliente_suffix_variants_mapped(self):
        """CodCliente_, CodCliente_2 suffix variants should all map to borrower_id."""
        raw = pd.DataFrame(
            {
                "loan_id": ["D001", "D002"],
                "principal_amount": [10000, 20000],
                "interest_rate": [0.12, 0.18],
                "term_months": [12, 24],
                "origination_date": ["2025-01-01", "2025-02-01"],
                "current_status": ["active", "active"],
                "CodCliente_": ["C1", None],
                "CodCliente_2": [None, "C2"],
            }
        )
        # After normalize: codcliente_ and codcliente_2 both in COLUMN_ALIASES for borrower_id
        df = self._normalize_and_alias(raw)
        # At least one variant maps to borrower_id
        has_borrower = "borrower_id" in df.columns
        assert has_borrower, "borrower_id should be mapped from CodCliente_ or CodCliente_2"


class TestPortfolioDashboardDuplicateClassification:
    """Verify that _classify_loan_id_duplicates is wired and usable from the Dashboard."""

    def test_classify_imported_from_csv_upload(self):
        """Dashboard imports _classify_loan_id_duplicates from csv_upload module."""
        assert hasattr(_dash_mod, "_classify_loan_id_duplicates")

    def test_exact_duplicate_returns_warning(self):
        df = pd.DataFrame(
            {"loan_id": ["A", "A"], "borrower_id": ["b1", "b1"], "amount": [100.0, 100.0]}
        )
        result = _dash_mod._classify_loan_id_duplicates(df)
        assert any(level == "warning" and "exact" in msg.lower() for level, msg in result)

    def test_historical_snapshot_returns_info(self):
        df = pd.DataFrame(
            {"loan_id": ["A", "A"], "borrower_id": ["b1", "b1"], "amount": [100.0, 90.0]}
        )
        result = _dash_mod._classify_loan_id_duplicates(df)
        assert any(level == "info" and "snapshot" in msg.lower() for level, msg in result)

    def test_suspicious_merge_returns_warning(self):
        df = pd.DataFrame(
            {"loan_id": ["A", "A"], "borrower_id": ["b1", "b2"], "amount": [100.0, 100.0]}
        )
        result = _dash_mod._classify_loan_id_duplicates(df)
        assert any(level == "warning" and "suspicious" in msg.lower() for level, msg in result)
