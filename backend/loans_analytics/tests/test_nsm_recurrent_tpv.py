import pandas as pd
import pytest
from backend.src.pipeline.calculation import CalculationPhase

def _make_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)

class TestBuildClientTpvTimeseries:

    def test_basic_aggregation(self):
        df = _make_df([{'client_id': 'A', 'origination_date': '2026-01-10', 'amount': 100.0}, {'client_id': 'A', 'origination_date': '2026-01-20', 'amount': 200.0}, {'client_id': 'B', 'origination_date': '2026-01-15', 'amount': 150.0}, {'client_id': 'A', 'origination_date': '2026-02-05', 'amount': 50.0}])
        result = CalculationPhase._build_client_tpv_timeseries(df)
        assert set(result.columns) == {'period', 'client_id', 'tpv'}  # nosec B101
        a_jan = result.loc[(result['client_id'] == 'A') & (result['period'] == '2026-01'), 'tpv'].iloc[0]
        assert a_jan == pytest.approx(300.0)  # nosec B101
        b_jan = result.loc[(result['client_id'] == 'B') & (result['period'] == '2026-01'), 'tpv'].iloc[0]
        assert b_jan == pytest.approx(150.0)  # nosec B101
        a_feb = result.loc[(result['client_id'] == 'A') & (result['period'] == '2026-02'), 'tpv'].iloc[0]
        assert a_feb == pytest.approx(50.0)  # nosec B101

    def test_empty_dataframe_returns_empty(self):
        result = CalculationPhase._build_client_tpv_timeseries(pd.DataFrame())
        assert result.empty  # nosec B101
        assert list(result.columns) == ['period', 'client_id', 'tpv']  # nosec B101

    def test_missing_required_columns_returns_empty(self):
        df = _make_df([{'foo': 1, 'bar': 2}])
        result = CalculationPhase._build_client_tpv_timeseries(df)
        assert result.empty  # nosec B101

    def test_alternative_column_names(self):
        df = _make_df([{'borrower_id': 'C1', 'FechaDesembolso': '2026-03-01', 'MontoDesembolsado': 500.0}])
        result = CalculationPhase._build_client_tpv_timeseries(df)
        assert len(result) == 1  # nosec B101
        assert result.iloc[0]['client_id'] == 'C1'  # nosec B101
        assert result.iloc[0]['period'] == '2026-03'  # nosec B101
        assert result.iloc[0]['tpv'] == pytest.approx(500.0)  # nosec B101

    def test_invalid_dates_dropped(self):
        df = _make_df([{'client_id': 'A', 'origination_date': 'not-a-date', 'amount': 100.0}, {'client_id': 'B', 'origination_date': '2026-01-01', 'amount': 200.0}])
        result = CalculationPhase._build_client_tpv_timeseries(df)
        assert len(result) == 1  # nosec B101
        assert result.iloc[0]['client_id'] == 'B'  # nosec B101

class TestCalculateRecurrentTpv:

    def _make_ts(self) -> pd.DataFrame:
        return _make_df([{'period': '2026-01', 'client_id': 'A', 'tpv': 100.0}, {'period': '2026-01', 'client_id': 'B', 'tpv': 200.0}, {'period': '2026-02', 'client_id': 'A', 'tpv': 150.0}, {'period': '2026-02', 'client_id': 'C', 'tpv': 50.0}, {'period': '2026-03', 'client_id': 'A', 'tpv': 120.0}, {'period': '2026-03', 'client_id': 'B', 'tpv': 80.0}, {'period': '2026-03', 'client_id': 'C', 'tpv': 60.0}])

    def test_returns_expected_keys(self):
        result = CalculationPhase._calculate_recurrent_tpv(self._make_ts())
        assert 'by_period' in result  # nosec B101
        assert 'latest_period' in result  # nosec B101
        assert 'latest' in result  # nosec B101

    def test_first_period_all_new(self):
        result = CalculationPhase._calculate_recurrent_tpv(self._make_ts())
        jan = result['by_period']['2026-01']
        assert jan['new_clients'] == 2  # nosec B101
        assert jan['recurrent_clients'] == 0  # nosec B101
        assert jan['recovered_clients'] == 0  # nosec B101
        assert jan['tpv_new'] == pytest.approx(300.0)  # nosec B101
        assert jan['tpv_recurrent'] == pytest.approx(0.0)  # nosec B101

    def test_second_period_recurrent_and_new(self):
        result = CalculationPhase._calculate_recurrent_tpv(self._make_ts())
        feb = result['by_period']['2026-02']
        assert feb['recurrent_clients'] == 1  # nosec B101
        assert feb['new_clients'] == 1  # nosec B101
        assert feb['recovered_clients'] == 0  # nosec B101
        assert feb['tpv_recurrent'] == pytest.approx(150.0)  # nosec B101
        assert feb['tpv_new'] == pytest.approx(50.0)  # nosec B101

    def test_third_period_recovered(self):
        result = CalculationPhase._calculate_recurrent_tpv(self._make_ts())
        mar = result['by_period']['2026-03']
        assert mar['recurrent_clients'] == 2  # nosec B101
        assert mar['recovered_clients'] == 1  # nosec B101
        assert mar['new_clients'] == 0  # nosec B101
        assert mar['tpv_recurrent'] == pytest.approx(180.0)  # nosec B101
        assert mar['tpv_recovered'] == pytest.approx(80.0)  # nosec B101

    def test_latest_period_and_latest_match(self):
        result = CalculationPhase._calculate_recurrent_tpv(self._make_ts())
        assert result['latest_period'] == '2026-03'  # nosec B101
        assert result['latest'] == result['by_period']['2026-03']  # nosec B101

    def test_empty_input_returns_empty_dict(self):
        result = CalculationPhase._calculate_recurrent_tpv(pd.DataFrame(columns=['period', 'client_id', 'tpv']))
        assert result == {}  # nosec B101

    def test_single_period(self):
        ts = _make_df([{'period': '2026-01', 'client_id': 'X', 'tpv': 999.0}])
        result = CalculationPhase._calculate_recurrent_tpv(ts)
        assert result['latest_period'] == '2026-01'  # nosec B101
        jan = result['by_period']['2026-01']
        assert jan['new_clients'] == 1  # nosec B101
        assert jan['recurrent_clients'] == 0  # nosec B101
        assert jan['tpv_new'] == pytest.approx(999.0)  # nosec B101

    def test_single_client_multi_period(self):
        ts = _make_df([{'period': '2026-01', 'client_id': 'Solo', 'tpv': 100.0}, {'period': '2026-02', 'client_id': 'Solo', 'tpv': 200.0}, {'period': '2026-03', 'client_id': 'Solo', 'tpv': 300.0}])
        result = CalculationPhase._calculate_recurrent_tpv(ts)
        assert result['by_period']['2026-01']['new_clients'] == 1  # nosec B101
        assert result['by_period']['2026-02']['recurrent_clients'] == 1  # nosec B101
        assert result['by_period']['2026-03']['recurrent_clients'] == 1  # nosec B101

    def test_tpv_totals_rounded_to_two_decimals(self):
        ts = _make_df([{'period': '2026-01', 'client_id': 'A', 'tpv': 1.0 / 3}])
        result = CalculationPhase._calculate_recurrent_tpv(ts)
        tpv_total = result['by_period']['2026-01']['tpv_total']
        assert tpv_total == round(1.0 / 3, 2)  # nosec B101

    def test_schema_fields_present(self):
        result = CalculationPhase._calculate_recurrent_tpv(self._make_ts())
        for period_data in result['by_period'].values():
            for key in ('tpv_total', 'tpv_new', 'tpv_recurrent', 'tpv_recovered', 'active_clients', 'new_clients', 'recurrent_clients', 'recovered_clients'):
                assert key in period_data  # nosec B101

class TestCalculationPhaseProcessPublishesNsmPayload:

    def test_process_includes_nsm_recurrent_tpv(self, monkeypatch):
        df = _make_df([{'client_id': 'A', 'origination_date': '2026-01-10', 'amount': 100.0, 'days_past_due': 0.0}, {'client_id': 'A', 'origination_date': '2026-02-15', 'amount': 150.0, 'days_past_due': 0.0}, {'client_id': 'B', 'origination_date': '2026-02-18', 'amount': 50.0, 'days_past_due': 45.0}])
        phase = CalculationPhase(config={}, kpi_definitions={})
        monkeypatch.setattr(phase.engine, 'calculate', lambda frame: {'portfolio': 1.0})
        monkeypatch.setattr(phase, '_calculate_segment_kpis', lambda frame: {})
        monkeypatch.setattr(phase, '_calculate_time_series', lambda frame: {'monthly': []})
        monkeypatch.setattr(phase, '_run_advanced_clustering', lambda frame: {})
        monkeypatch.setattr(phase, '_detect_anomalies', lambda kpis: [])
        monkeypatch.setattr(phase, '_generate_manifest', lambda kpis, frame: {})
        result = phase.process(df)
        assert 'nsm_recurrent_tpv' in result  # nosec B101
        assert result['nsm_recurrent_tpv']['latest_period'] == '2026-02'  # nosec B101
        assert result['nsm_recurrent_tpv']['latest']['tpv_recurrent'] == pytest.approx(150.0)  # nosec B101
