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
