import json
import os
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from backend.src.pipeline.output import OutputPhase, _parse_bool_env

def _output(config_overrides=None) -> OutputPhase:
    config = {'database': {'enabled': True, 'table': 'kpi_values'}}
    if config_overrides:
        config['database'].update(config_overrides)
    return OutputPhase(config)

def test_is_monitoring_kpi_values_table_variants():
    output = _output()
    assert output._is_monitoring_kpi_values_table('kpi_values') is True
    assert output._is_monitoring_kpi_values_table('public.kpi_values') is True
    assert output._is_monitoring_kpi_values_table('monitoring.kpi_values') is True
    assert output._is_monitoring_kpi_values_table('kpi_timeseries_daily') is False

def test_prepare_kpi_rows_uses_monitoring_shape_for_public_view_name():
    output = _output()
    rows, _, _ = output._prepare_kpi_rows({'par_30': 6.1})
    assert len(rows) == 1
    assert rows[0]['kpi_name'] == 'par_30'
    assert rows[0]['value'] == pytest.approx(6.1)
    assert 'kpi_value' not in rows[0]

def test_map_monitoring_kpi_name_default_aliases():
    output = _output()
    assert output._map_monitoring_kpi_name('default_rate') == 'default_rate'
    assert output._map_monitoring_kpi_name('disbursement_volume_mtd') == 'disbursement_volume_mtd'

def test_map_monitoring_kpi_name_custom_alias_overrides_defaults():
    output = _output({'kpi_name_aliases': {'default_rate': 'default_rate_custom'}})
    assert output._map_monitoring_kpi_name('default_rate') == 'default_rate_custom'

def test_insert_batch_rows_monitoring_uses_upsert_and_conflict_keys():
    output = _output()
    supabase = MagicMock()
    query = MagicMock()
    supabase.schema.return_value.table.return_value = query
    query.upsert.return_value.execute.return_value = MagicMock()
    rows = [{'kpi_name': 'default_rate', 'value': 2.5, 'timestamp': '2026-02-23T00:00:00', 'status': 'green'}]
    with patch.object(output, '_get_kpi_definitions_map', return_value=({'default_rate': 'default_rate'}, {'default_rate': 3})):
        inserted = output._insert_batch_rows(supabase, 'kpi_values', rows)
    assert inserted == 1
    query.upsert.assert_called_once()
    upsert_rows = query.upsert.call_args.args[0]
    assert len(upsert_rows) == 1
    assert upsert_rows[0]['kpi_key'] == 'default_rate'
    assert upsert_rows[0]['kpi_id'] == 3
    assert query.upsert.call_args.kwargs['on_conflict'] == 'as_of_date,kpi_key,snapshot_id'

def test_execute_exports_segment_snapshot_when_clean_data_available(tmp_path):
    output = OutputPhase({'database': {'enabled': False}})
    clean_df = pd.DataFrame([{'loan_id': 'L1', 'outstanding_balance': 100.0, 'status': 'active', 'dpd': 0, 'company': 'Abaco Financial', 'credit_line': 'SME', 'kam_hunter': 'H1', 'kam_farmer': 'F1', 'origination_date': '2026-02-26', 'interest_rate': 0.12}, {'loan_id': 'L2', 'outstanding_balance': 200.0, 'status': 'defaulted', 'dpd': 120, 'company': 'Abaco Financial', 'credit_line': 'SME', 'kam_hunter': 'H1', 'kam_farmer': 'F1', 'origination_date': '2026-02-26', 'interest_rate': 0.18}])
    clean_df.to_parquet(tmp_path / 'clean_data.parquet', index=False)
    result = output.execute({'par_30': 12.3}, run_dir=tmp_path)
    assert result['status'] == 'success'
    assert 'segment_snapshot' in result['exports']
    segment_snapshot_path = tmp_path / 'segment_snapshot.json'
    assert segment_snapshot_path.exists()
    with open(segment_snapshot_path, 'r', encoding='utf-8') as file_handle:
        payload = json.load(file_handle)
    assert payload['run_id'] == tmp_path.name
    assert 'company' in payload['dimensions']
    assert payload['dimensions']['company'][0]['loan_count'] == 2

def test_execute_exports_full_ml_intelligence_payload(tmp_path):
    output = OutputPhase({'database': {'enabled': False}})
    segment_kpis = {'product_type': [{'segment': 'SME', 'par_30': 5.0}]}
    time_series = {'dates': ['2026-01-31'], 'par_30': [5.0]}
    anomalies = [{'kpi': 'default_rate', 'value': 42.0, 'severity': 'high'}]
    nsm_tpv = {'total_tpv': 1000000, 'recurrent_clients': 12}
    result = output.execute(kpi_results={'par_30': 5.0}, run_dir=tmp_path, segment_kpis=segment_kpis, time_series=time_series, anomalies=anomalies, nsm_recurrent_tpv=nsm_tpv)
    assert result['status'] == 'success'
    exports = result['exports']
    assert 'segment_kpis' in exports
    assert (tmp_path / 'segment_kpis.json').exists()
    assert 'time_series' in exports
    assert (tmp_path / 'time_series.json').exists()
    assert 'anomalies' in exports
    assert (tmp_path / 'anomalies.json').exists()
    assert 'nsm_recurrent_tpv' in exports
    assert (tmp_path / 'nsm_recurrent_tpv_output.json').exists()
    with open(tmp_path / 'anomalies.json', encoding='utf-8') as fh:
        saved = json.load(fh)
    assert saved[0]['kpi'] == 'default_rate'

def test_execute_exports_empty_payload_when_not_none(tmp_path):
    output = OutputPhase({'database': {'enabled': False}})
    result = output.execute(kpi_results={'par_30': 3.1}, run_dir=tmp_path, anomalies=[], time_series={})
    assert result['status'] == 'success'
    exports = result['exports']
    assert 'anomalies' in exports
    assert (tmp_path / 'anomalies.json').exists()
    with open(tmp_path / 'anomalies.json', encoding='utf-8') as fh:
        assert json.load(fh) == []
    assert 'time_series' in exports
    assert (tmp_path / 'time_series.json').exists()

def test_execute_omits_payload_keys_when_not_supplied(tmp_path):
    output = OutputPhase({'database': {'enabled': False}})
    result = output.execute(kpi_results={'par_30': 3.1}, run_dir=tmp_path)
    assert result['status'] == 'success'
    assert 'segment_kpis' not in result['exports']
    assert 'time_series' not in result['exports']
    assert 'anomalies' not in result['exports']
    assert 'nsm_recurrent_tpv' not in result['exports']

def test_quality_score_is_fail_closed_without_kpi_engine():
    output = OutputPhase({'database': {'enabled': False}})
    score = output._calculate_quality_score({'par_30': 4.2}, kpi_engine=None)
    assert score == pytest.approx(0.0)

def test_check_sla_is_fail_closed_without_kpi_engine():
    output = OutputPhase({'database': {'enabled': False}})
    assert output._check_sla({'par_30': 4.2}, kpi_engine=None) is False

def test_quality_score_is_fail_closed_for_malformed_audit_trail():
    output = OutputPhase({'database': {'enabled': False}})
    kpi_engine = MagicMock()
    kpi_engine.get_audit_trail.return_value = pd.DataFrame([{'unexpected': 'column'}])
    score = output._calculate_quality_score({'par_30': 4.2}, kpi_engine=kpi_engine)
    assert score == pytest.approx(0.0)

def test_check_sla_is_fail_closed_for_malformed_audit_trail():
    output = OutputPhase({'database': {'enabled': False}})
    kpi_engine = MagicMock()
    kpi_engine.get_audit_trail.return_value = pd.DataFrame([{'unexpected': 'column'}])
    assert output._check_sla({'par_30': 4.2}, kpi_engine=kpi_engine) is False


# ---------------------------------------------------------------------------
# Tests for _parse_bool_env helper
# ---------------------------------------------------------------------------


def test_parse_bool_env_unset_returns_default_true():
    with patch.dict(os.environ, {}, clear=True):
        assert _parse_bool_env('MISSING_VAR', default=True) is True


def test_parse_bool_env_unset_returns_default_false():
    with patch.dict(os.environ, {}, clear=True):
        assert _parse_bool_env('MISSING_VAR', default=False) is False


def test_parse_bool_env_truthy_values():
    for val in ('1', 'true', 'True', 'TRUE', 'yes', 'YES', 'on', 'ON'):
        with patch.dict(os.environ, {'MY_FLAG': val}):
            assert _parse_bool_env('MY_FLAG') is True, f'Expected True for {val!r}'


def test_parse_bool_env_falsy_values():
    for val in ('0', 'false', 'False', 'FALSE', 'no', 'NO', 'off', 'OFF'):
        with patch.dict(os.environ, {'MY_FLAG': val}):
            assert _parse_bool_env('MY_FLAG') is False, f'Expected False for {val!r}'


def test_parse_bool_env_raises_on_unrecognised_value():
    with patch.dict(os.environ, {'MY_FLAG': 'maybe'}):
        with pytest.raises(ValueError, match='unrecognised boolean value'):
            _parse_bool_env('MY_FLAG')


# ---------------------------------------------------------------------------
# Tests for _ensure_missing_kpi_definitions behaviour and compat shim
# ---------------------------------------------------------------------------


def _make_output(strict_kpi_definitions=None):
    db_cfg: dict = {'enabled': True, 'table': 'kpi_values'}
    if strict_kpi_definitions is not None:
        db_cfg['strict_kpi_definitions'] = strict_kpi_definitions
    return OutputPhase({'database': db_cfg})


def test_ensure_missing_kpi_raises_by_default():
    output = _make_output()
    with pytest.raises(RuntimeError, match='Missing KPI definitions'):
        output._ensure_missing_kpi_definitions({'new_kpi'}, set())


def test_ensure_missing_kpi_raises_when_no_config_key_and_no_env(monkeypatch):
    monkeypatch.delenv('PIPELINE_STRICT_KPI_DEFINITIONS', raising=False)
    output = _make_output()
    with pytest.raises(RuntimeError, match='Missing KPI definitions'):
        output._ensure_missing_kpi_definitions({'new_kpi'}, set())


def test_ensure_missing_kpi_disabled_via_config_false():
    output = _make_output(strict_kpi_definitions=False)
    # Should warn, not raise
    with patch('backend.src.pipeline.output.logger') as mock_log:
        output._ensure_missing_kpi_definitions({'new_kpi'}, set())
    mock_log.warning.assert_called()
    warning_msg = mock_log.warning.call_args[0][0]
    assert 'Missing KPI definitions' in warning_msg


def test_ensure_missing_kpi_disabled_via_env_false(monkeypatch):
    monkeypatch.setenv('PIPELINE_STRICT_KPI_DEFINITIONS', 'false')
    output = _make_output()
    with patch('backend.src.pipeline.output.logger') as mock_log:
        output._ensure_missing_kpi_definitions({'new_kpi'}, set())
    mock_log.warning.assert_called()


def test_ensure_missing_kpi_legacy_truthy_config_logs_deprecation(monkeypatch):
    monkeypatch.delenv('PIPELINE_STRICT_KPI_DEFINITIONS', raising=False)
    output = _make_output(strict_kpi_definitions=True)
    with patch('backend.src.pipeline.output.logger') as mock_log:
        with pytest.raises(RuntimeError, match='Missing KPI definitions'):
            output._ensure_missing_kpi_definitions({'new_kpi'}, set())
    # Deprecation warning must have been logged
    warning_calls = [str(c) for c in mock_log.warning.call_args_list]
    assert any('deprecated' in w for w in warning_calls)


def test_ensure_missing_kpi_legacy_truthy_env_logs_deprecation(monkeypatch):
    monkeypatch.setenv('PIPELINE_STRICT_KPI_DEFINITIONS', '1')
    output = _make_output()
    with patch('backend.src.pipeline.output.logger') as mock_log:
        with pytest.raises(RuntimeError, match='Missing KPI definitions'):
            output._ensure_missing_kpi_definitions({'new_kpi'}, set())
    warning_calls = [str(c) for c in mock_log.warning.call_args_list]
    assert any('deprecated' in w for w in warning_calls)


def test_ensure_missing_kpi_no_op_when_all_present():
    output = _make_output()
    # No error, no warning when nothing is missing
    output._ensure_missing_kpi_definitions({'kpi_a', 'kpi_b'}, {'kpi_a', 'kpi_b', 'kpi_c'})
