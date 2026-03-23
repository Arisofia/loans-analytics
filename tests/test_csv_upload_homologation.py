from __future__ import annotations
import sys
import types
import pandas as pd
import pytest
_st_stub = types.ModuleType('streamlit')
for _attr in ['error', 'warning', 'info', 'success', 'header', 'markdown', 'file_uploader', 'button', 'progress', 'empty', 'expander', 'dataframe', 'metric', 'columns', 'subheader', 'download_button', 'exception', 'stop', 'set_page_config']:
    setattr(_st_stub, _attr, lambda *a, **k: None)
sys.modules['streamlit'] = _st_stub
from frontend.streamlit_app.components.csv_upload import _alias_matches, _apply_aliases, _canonicalize_status, _classify_loan_id_duplicates, _coerce_numeric, _derive_status, _normalize_column_names, _prepare_dataframe, _validate_for_pipeline, BORROWER_ID_COLS

class TestCoerceNumeric:

    def test_dollar_sign_and_thousands(self):
        s = pd.Series(['$50,000', '$1,234.56', '10000', ''])
        out = _coerce_numeric(s)
        assert out.iloc[0] == pytest.approx(50000.0)
        assert out.iloc[1] == pytest.approx(1234.56)
        assert out.iloc[2] == pytest.approx(10000.0)
        assert out.iloc[3] == pytest.approx(0.0)

    def test_plain_integers(self):
        s = pd.Series(['100', '200', '300'])
        out = _coerce_numeric(s)
        assert list(out) == pytest.approx([100.0, 200.0, 300.0])

    def test_decimal_comma_locale(self):
        s = pd.Series(['1234,56'])
        out = _coerce_numeric(s)
        assert out.iloc[0] == pytest.approx(1234.56)

    def test_nan_and_none(self):
        s = pd.Series([None, 'nan', 'NaN', 'None'])
        out = _coerce_numeric(s)
        assert list(out) == pytest.approx([0.0, 0.0, 0.0, 0.0])

class TestAliasMatches:

    def test_exact_match(self):
        cols = ['codcliente', 'other']
        assert _alias_matches(cols, 'codcliente') == ['codcliente']

    def test_trailing_underscore(self):
        cols = ['codcliente_', 'codcliente__']
        result = _alias_matches(cols, 'codcliente')
        assert 'codcliente_' in result
        assert 'codcliente__' in result

    def test_numeric_suffix(self):
        cols = ['codcliente1', 'codcliente2', 'codcliente_2']
        result = _alias_matches(cols, 'codcliente')
        assert 'codcliente1' in result
        assert 'codcliente2' in result
        assert 'codcliente_2' in result

    def test_kam_hunter_variants(self):
        cols = ['cod_kam_hunter', 'cod_kam_hunter_', 'cod_kam_hunter1']
        result = _alias_matches(cols, 'cod_kam_hunter')
        assert set(result) == set(cols)

    def test_no_spurious_matches(self):
        cols = ['codclienteX_extra', 'notcodcliente']
        result = _alias_matches(cols, 'codcliente')
        assert result == []

class TestApplyAliases:

    def _make_desembolsos_df(self) -> pd.DataFrame:
        return pd.DataFrame({'numero_desembolso': ['D001', 'D002'], 'monto_del_desembolso': ['$50,000', '$30,000'], 'codcliente': ['C1', 'C2'], 'estado': ['Vigente', 'Mora'], 'dias_mora': [0, 35]})

    def test_loan_id_mapped_from_numero_desembolso(self):
        df = _normalize_column_names(self._make_desembolsos_df())
        mapped = _apply_aliases(df)
        assert 'loan_id' in mapped.columns
        assert list(mapped['loan_id']) == ['D001', 'D002']

    def test_borrower_id_mapped_from_codcliente(self):
        df = _normalize_column_names(self._make_desembolsos_df())
        mapped = _apply_aliases(df)
        assert 'borrower_id' in mapped.columns
        assert list(mapped['borrower_id']) == ['C1', 'C2']

    def test_amount_mapped_and_currency_parsed(self):
        raw = pd.DataFrame({'numero_desembolso': ['D001'], 'monto_del_desembolso': ['$50,000']})
        prepared = _prepare_dataframe(raw)
        assert 'amount' in prepared.columns
        assert prepared['amount'].iloc[0] == pytest.approx(50000.0)

    def test_codcliente_suffix_variants_coalesced(self):
        raw = pd.DataFrame({'numero_desembolso': ['D001', 'D002'], 'CodCliente_': ['C1', None], 'CodCliente_2': [None, 'C2']})
        prepared = _prepare_dataframe(raw)
        assert 'borrower_id' in prepared.columns
        assert prepared['borrower_id'].iloc[0] == 'C1'
        assert prepared['borrower_id'].iloc[1] == 'C2'

class TestClassifyLoanIdDuplicates:

    def test_no_duplicates_returns_empty(self):
        df = pd.DataFrame({'loan_id': ['A', 'B', 'C'], 'borrower_id': ['b1', 'b2', 'b3'], 'amount': [100.0, 200.0, 300.0]})
        assert _classify_loan_id_duplicates(df) == []

    def test_exact_duplicate_emits_warning(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b1'], 'amount': [100.0, 100.0]})
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, msg = result[0]
        assert level == 'warning'
        assert 'exact duplicate' in msg.lower()

    def test_historical_snapshot_emits_info(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b1'], 'amount': [100.0, 90.0]})
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, msg = result[0]
        assert level == 'info'
        assert 'snapshot' in msg.lower()

    def test_suspicious_merge_emits_warning(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b2'], 'amount': [100.0, 100.0]})
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, msg = result[0]
        assert level == 'warning'
        assert 'suspicious' in msg.lower()

    def test_mixed_scenarios_all_reported(self):
        df = pd.DataFrame({'loan_id': ['A', 'A', 'B', 'B', 'C', 'C'], 'borrower_id': ['b1', 'b1', 'b2', 'b2', 'b3', 'b4'], 'amount': [100.0, 100.0, 200.0, 150.0, 300.0, 300.0]})
        result = _classify_loan_id_duplicates(df)
        warning_msgs = [msg for level, msg in result if level == 'warning']
        info_msgs = [msg for level, msg in result if level == 'info']
        assert len(info_msgs) == 1
        assert len(warning_msgs) == 2

    def test_missing_loan_id_column_returns_empty(self):
        df = pd.DataFrame({'amount': [100.0]})
        assert _classify_loan_id_duplicates(df) == []

    def test_no_borrower_id_column_falls_back_to_generic(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'amount': [100.0, 80.0]})
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, _ = result[0]
        assert level == 'warning'

    def test_no_borrower_id_same_amount_falls_back_to_generic(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'amount': [100.0, 100.0]})
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, _ = result[0]
        assert level == 'warning'

    def test_client_code_used_as_borrower_fallback(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'client_code': ['C1', 'C1'], 'amount': [100.0, 100.0]})
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, _ = result[0]
        assert level == 'warning'

    def test_client_name_used_as_borrower_fallback(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'client_name': ['Alice', 'Bob'], 'amount': [100.0, 100.0]})
        result = _classify_loan_id_duplicates(df)
        assert len(result) == 1
        level, msg = result[0]
        assert level == 'warning'
        assert 'suspicious' in msg.lower()

    def test_borrower_id_takes_priority_over_client_code(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b2'], 'client_code': ['C1', 'C1'], 'amount': [100.0, 100.0]})
        result = _classify_loan_id_duplicates(df)
        assert any(('suspicious' in msg.lower() for _, msg in result))

    def test_borrower_id_cols_constant_priority(self):
        assert BORROWER_ID_COLS[0] == 'borrower_id'
        assert 'client_code' in BORROWER_ID_COLS
        assert 'client_name' in BORROWER_ID_COLS

class TestValidateForPipeline:

    def test_valid_frame_returns_true(self):
        df = pd.DataFrame({'loan_id': ['A'], 'amount': [100.0], 'status': ['active']})
        valid, missing, issues, notices = _validate_for_pipeline(df)
        assert valid is True
        assert missing == []
        assert issues == []
        assert notices == []

    def test_missing_required_columns(self):
        df = pd.DataFrame({'loan_id': ['A']})
        valid, missing, issues, notices = _validate_for_pipeline(df)
        assert valid is False
        assert 'amount' in missing
        assert 'status' in missing
        assert isinstance(issues, list)
        assert isinstance(notices, list)

    def test_all_zeros_amount_reported(self):
        df = pd.DataFrame({'loan_id': ['A'], 'amount': [0.0], 'status': ['active']})
        valid, missing, issues, notices = _validate_for_pipeline(df)
        assert valid is True
        assert any(('zero' in i.lower() for i in issues))
        assert isinstance(notices, list)
import importlib.util as _ilu
import os as _os
from unittest.mock import patch as _patch
import plotly.express
import plotly.graph_objects
for _attr in ['session_state', 'cache_data', 'cache_resource', 'spinner', 'tabs', 'plotly_chart', 'selectbox', 'checkbox', 'radio', 'text_input', 'number_input', 'caption', 'write', 'sidebar']:
    setattr(_st_stub, _attr, lambda *a, **k: None)
setattr(_st_stub, 'session_state', {})
_os.environ.setdefault('ABACO_API_BASE', 'http://localhost:8000')
_dash_spec = _ilu.spec_from_file_location('_portfolio_dashboard_test', str(__import__('pathlib').Path(__file__).parent.parent / 'frontend' / 'streamlit_app' / 'pages' / '3_Portfolio_Dashboard.py'))
assert _dash_spec is not None
_dash_mod = _ilu.module_from_spec(_dash_spec)
with _patch('pathlib.Path.mkdir'):
    assert _dash_spec.loader is not None
    _dash_spec.loader.exec_module(_dash_mod)

class TestPortfolioDashboardDesembolsos:

    def _desembolsos_raw(self) -> pd.DataFrame:
        return pd.DataFrame({'Numero_Desembolso': ['D001', 'D002'], 'Monto_del_Desembolso': ['$50,000', '$30,000'], 'CodCliente': ['C1', 'C2'], 'Estado': ['Vigente', 'Mora'], 'Tasa_de_Interes': [0.12, 0.18], 'Plazo_Meses': [12, 24], 'Fecha_Desembolso': ['2025-01-01', '2025-02-01']})

    def _normalize_and_alias(self, raw: pd.DataFrame) -> pd.DataFrame:
        return _dash_mod._apply_column_aliases(_dash_mod._normalize_column_names(raw))

    def test_numero_desembolso_mapped_to_loan_id(self):
        df = self._normalize_and_alias(self._desembolsos_raw())
        assert 'loan_id' in df.columns
        assert list(df['loan_id']) == ['D001', 'D002']

    def test_codcliente_mapped_to_borrower_id(self):
        df = self._normalize_and_alias(self._desembolsos_raw())
        assert 'borrower_id' in df.columns
        assert list(df['borrower_id']) == ['C1', 'C2']

    def test_monto_del_desembolso_mapped_to_principal_amount(self):
        df = self._normalize_and_alias(self._desembolsos_raw())
        assert 'principal_amount' in df.columns
        assert df['principal_amount'].notna().all()

    def test_currency_parsed_correctly_in_prepare(self):
        raw = self._desembolsos_raw()
        aliased = self._normalize_and_alias(raw)
        prepared = _dash_mod.prepare_uploaded_data(aliased)
        assert 'principal_amount' in prepared.columns
        assert prepared['principal_amount'].iloc[0] == pytest.approx(50000.0)
        assert prepared['principal_amount'].iloc[1] == pytest.approx(30000.0)

    def test_dias_mora_mapped_to_days_past_due(self):
        raw = pd.DataFrame({'loan_id': ['D001'], 'principal_amount': [10000.0], 'interest_rate': [0.12], 'term_months': [12], 'origination_date': ['2025-01-01'], 'current_status': ['active'], 'Dias_Mora': [35]})
        df = self._normalize_and_alias(raw)
        assert 'days_past_due' in df.columns

    def test_origination_date_aliased_from_fecha_desembolso(self):
        df = self._normalize_and_alias(self._desembolsos_raw())
        assert 'origination_date' in df.columns

    def test_codcliente_suffix_variants_not_directly_aliased(self):
        raw = pd.DataFrame({'loan_id': ['D001', 'D002'], 'principal_amount': [10000, 20000], 'interest_rate': [0.12, 0.18], 'term_months': [12, 24], 'origination_date': ['2025-01-01', '2025-02-01'], 'current_status': ['active', 'active'], 'CodCliente_': ['C1', None], 'CodCliente_2': [None, 'C2']})
        df = self._normalize_and_alias(raw)
        assert 'borrower_id' not in df.columns

class TestPortfolioDashboardDuplicateClassification:

    def test_classify_imported_from_csv_upload(self):
        assert hasattr(_dash_mod, '_classify_loan_id_duplicates')

    def test_exact_duplicate_returns_warning(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b1'], 'amount': [100.0, 100.0]})
        result = _dash_mod._classify_loan_id_duplicates(df)
        assert any((level == 'warning' and 'exact' in msg.lower() for level, msg in result))

    def test_historical_snapshot_returns_info(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b1'], 'amount': [100.0, 90.0]})
        result = _dash_mod._classify_loan_id_duplicates(df)
        assert any((level == 'info' and 'snapshot' in msg.lower() for level, msg in result))

    def test_suspicious_merge_returns_warning(self):
        df = pd.DataFrame({'loan_id': ['A', 'A'], 'borrower_id': ['b1', 'b2'], 'amount': [100.0, 100.0]})
        result = _dash_mod._classify_loan_id_duplicates(df)
        assert any((level == 'warning' and 'suspicious' in msg.lower() for level, msg in result))

class TestCanonicalizeStatusNullHandling:

    def test_none_returns_unknown(self):
        assert _canonicalize_status(None) == 'unknown'

    def test_empty_string_returns_unknown(self):
        assert _canonicalize_status('') == 'unknown'

    def test_nan_string_returns_unknown(self):
        assert _canonicalize_status('nan') == 'unknown'

    def test_nan_float_returns_unknown(self):
        import math
        assert _canonicalize_status(math.nan) == 'unknown'

    def test_whitespace_only_returns_unknown(self):
        assert _canonicalize_status('   ') == 'unknown'

    def test_known_active_aliases_still_work(self):
        for alias in ('active', 'current', 'vigente', 'open', 'in_force'):
            assert _canonicalize_status(alias) == 'active', f"expected 'active' for {alias!r}"

    def test_defaulted_aliases_unaffected(self):
        for alias in ('default', 'defaulted', 'charged_off'):
            assert _canonicalize_status(alias) == 'defaulted', f"expected 'defaulted' for {alias!r}"

class TestDeriveStatusNullResolution:

    def test_null_status_no_dpd_resolves_to_active(self):
        df = pd.DataFrame({'status': [None, ''], 'days_past_due': [0, 0]})
        result = _derive_status(df)
        assert list(result) == ['active', 'active']

    def test_null_status_dpd_30_resolves_to_delinquent(self):
        df = pd.DataFrame({'status': [None], 'days_past_due': [35]})
        result = _derive_status(df)
        assert result.iloc[0] == 'delinquent'

    def test_null_status_dpd_90_plus_resolves_to_defaulted(self):
        df = pd.DataFrame({'status': [None], 'days_past_due': [90]})
        result = _derive_status(df)
        assert result.iloc[0] == 'defaulted'

    def test_null_status_no_dpd_column_stays_unknown(self):
        df = pd.DataFrame({'status': [None, 'nan']})
        result = _derive_status(df)
        assert list(result) == ['unknown', 'unknown']

    def test_explicit_status_is_not_overridden_by_zero_dpd(self):
        df = pd.DataFrame({'status': ['delinquent'], 'days_past_due': [0]})
        result = _derive_status(df)
        assert result.iloc[0] == 'delinquent'
