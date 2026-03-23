from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

class TestZeroCostStorage:

    def test_write_and_read_parquet(self, tmp_path):
        from backend.src.zero_cost.storage import ZeroCostStorage
        storage = ZeroCostStorage(base_dir=tmp_path / 'data', db_path=None)
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        storage.write_parquet(df, 'test_table', write_manifest=True)
        parquet_files = list((tmp_path / 'data' / 'test_table').glob('*.parquet'))
        assert len(parquet_files) == 1
        manifest_files = list((tmp_path / 'data' / 'test_table').glob('*.manifest.json'))
        assert len(manifest_files) == 1

    def test_manifest_content(self, tmp_path):
        import json
        from backend.src.zero_cost.storage import ZeroCostStorage
        storage = ZeroCostStorage(base_dir=tmp_path / 'data', db_path=None)
        df = pd.DataFrame({'col1': [10, 20], 'col2': [0.1, 0.2]})
        storage.write_parquet(df, 'manifest_test')
        manifest_files = list((tmp_path / 'data' / 'manifest_test').glob('*.manifest.json'))
        content = json.loads(manifest_files[0].read_text())
        assert content['rows'] == 2
        assert 'sha256' in content
        assert 'col1' in content['columns']

    def test_duckdb_query(self, tmp_path):
        pytest.importorskip('duckdb')
        from backend.src.zero_cost.storage import ZeroCostStorage
        db_path = tmp_path / 'test.duckdb'
        storage = ZeroCostStorage(base_dir=tmp_path / 'data', db_path=db_path)
        df = pd.DataFrame({'id': [1, 2, 3], 'value': [100.0, 200.0, 300.0]})
        storage.write_parquet(df, 'query_test')
        result = storage.query('SELECT SUM(value) AS total FROM query_test')
        assert result['total'].iloc[0] == pytest.approx(600.0)
        storage.close()

class TestControlMoraAdapter:

    def _make_mora_csv(self, tmp_path, delimiter: str=',', filename: str='control_mora_ene2026.csv') -> Path:
        rows = ['NumeroDesembolso,lend_id,NombreCliente,SaldoVigente,TotalVencido,DPD,FechaDesembolso', 'NDE-001,L-100,Juan Perez,10000.00,500.00,15,2025-01-15', 'NDE-002,L-101,Maria Lopez,20000.00,0.00,0,2025-03-01', 'NDE-003,L-102,Carlos Ruiz,5000.00,5000.00,95,2024-11-20']
        p = tmp_path / filename
        p.write_text(delimiter.join(rows[0].split(',')) + '\n')
        with p.open('a') as f:
            for row in rows[1:]:
                f.write(delimiter.join(row.split(',')) + '\n')
        return p

    def test_load_basic(self, tmp_path):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        adapter = ControlMoraAdapter(snapshot_month='2026-01-31')
        df = adapter.load(self._make_mora_csv(tmp_path))
        assert len(df) == 3
        assert 'numero_desembolso' in df.columns
        assert 'lend_id' in df.columns
        assert 'client_name' in df.columns

    def test_column_aliasing(self, tmp_path):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        adapter = ControlMoraAdapter(snapshot_month='2026-01-31')
        df = adapter.load(self._make_mora_csv(tmp_path))
        assert 'principal_outstanding' in df.columns
        assert 'dpd' in df.columns

    def test_numeric_coercion(self, tmp_path):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        adapter = ControlMoraAdapter(snapshot_month='2026-01-31')
        df = adapter.load(self._make_mora_csv(tmp_path))
        assert df['principal_outstanding'].dtype in (float, 'float64')
        assert pd.api.types.is_integer_dtype(df['dpd'])

    def test_snapshot_month_inferred_from_filename(self, tmp_path):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        adapter = ControlMoraAdapter(snapshot_month=None)
        df = adapter.load(self._make_mora_csv(tmp_path))
        assert 'snapshot_month' in df.columns
        assert df['snapshot_month'].notna().all()

    def test_snapshot_month_inference_warning_on_unparseable_filename(self, tmp_path, caplog):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        adapter = ControlMoraAdapter(snapshot_month=None)
        csv_path = self._make_mora_csv(tmp_path, filename='control_mora_raw.csv')
        import logging
        with caplog.at_level(logging.WARNING, logger='src.zero_cost.control_mora_adapter'):
            df = adapter.load(csv_path)
        assert 'snapshot_month' in df.columns
        assert df['snapshot_month'].isna().all()
        assert any(('snapshot_month' in record.message for record in caplog.records))

    def test_snapshot_month_set(self, tmp_path):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        adapter = ControlMoraAdapter(snapshot_month='2026-01-31')
        df = adapter.load(self._make_mora_csv(tmp_path))
        assert df['snapshot_month'].iloc[0] == pd.Timestamp('2026-01-31')

    def test_mora_bucket_inference(self, tmp_path):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        adapter = ControlMoraAdapter(snapshot_month='2026-01-31')
        df = adapter.load(self._make_mora_csv(tmp_path))
        builder = MonthlySnapshotBuilder()
        snap = builder.build(df)
        buckets = snap.set_index('lend_id')['mora_bucket']
        assert buckets['L-100'] == '1-30'
        assert buckets['L-101'] == 'current'
        assert buckets['L-102'] == '91-180'

    def test_load_many(self, tmp_path):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        csv1 = self._make_mora_csv(tmp_path)
        (tmp_path / 'm2').mkdir(exist_ok=True)
        csv2 = self._make_mora_csv(tmp_path / 'm2')
        df = ControlMoraAdapter.load_many([csv1, csv2], snapshot_month='2026-01-31')
        assert len(df) == 3

class TestMonthlySnapshotBuilder:

    def _loans_df(self):
        return pd.DataFrame({'lend_id': ['L-1', 'L-2', 'L-3', 'L-4'], 'principal_outstanding': [10000, 20000, 5000, 8000], 'total_overdue_amount': [0, 2000, 5000, 0], 'dpd': [0, 35, 92, 0], 'disbursement_date': pd.to_datetime(['2025-01-01', '2025-03-15', '2024-11-01', '2025-06-01']), 'snapshot_month': pd.to_datetime(['2026-01-31'] * 4)})

    def test_build_returns_expected_columns(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        assert 'mora_bucket' in snap.columns
        assert 'par_30' in snap.columns
        assert 'par_90' in snap.columns
        assert 'months_on_book' in snap.columns

    def test_par_flags(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df()).set_index('lend_id')
        assert not snap.loc['L-1', 'par_1']
        assert snap.loc['L-2', 'par_30']
        assert snap.loc['L-3', 'par_90']
        assert not snap.loc['L-4', 'par_90']

    def test_compute_portfolio_kpis(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        kpis = builder.compute_portfolio_kpis(snap)
        assert kpis['total_loans'] == 4
        assert kpis['total_outstanding'] == pytest.approx(43000.0)
        assert kpis['total_overdue'] == pytest.approx(7000.0)

    def test_compute_portfolio_kpis_active_loans(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        kpis = builder.compute_portfolio_kpis(snap)
        assert kpis['active_loans'] == 4

    def test_compute_portfolio_kpis_active_loans_with_zero_outstanding(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        df = self._loans_df().copy()
        df.loc[df['lend_id'] == 'L-3', 'principal_outstanding'] = 0
        snap = builder.build(df)
        kpis = builder.compute_portfolio_kpis(snap)
        assert kpis['active_loans'] == 3

    def test_compute_portfolio_kpis_active_loans_fallback(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        df = self._loans_df().drop(columns=['principal_outstanding'])
        snap = builder.build(df)
        kpis = builder.compute_portfolio_kpis(snap)
        assert kpis['active_loans'] == kpis['total_loans']

    def test_compute_portfolio_kpis_weighted_avg_dpd(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        kpis = builder.compute_portfolio_kpis(snap)
        assert 'weighted_avg_dpd' in kpis
        assert kpis['weighted_avg_dpd'] == pytest.approx((0 * 10000 + 35 * 20000 + 92 * 5000 + 0 * 8000) / 43000.0, rel=0.0001)

    def test_set_snapshot_month_explicit_normalizes_to_month_end(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        df = self._loans_df().drop(columns=['snapshot_month'])
        result = builder.build(df, as_of_month='2026-02-15')
        expected = pd.Timestamp('2026-02-28')
        assert (result['snapshot_month'] == expected).all()

    def test_set_snapshot_month_column_normalizes_to_month_end(self):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        builder = MonthlySnapshotBuilder()
        df = self._loans_df().copy()
        df['snapshot_month'] = pd.to_datetime('2026-03-10')
        result = builder.build(df)
        expected = pd.Timestamp('2026-03-31')
        assert (result['snapshot_month'] == expected).all()

    def test_to_star_schema(self, tmp_path):
        from backend.src.zero_cost.monthly_snapshot import MonthlySnapshotBuilder
        from backend.src.zero_cost.storage import ZeroCostStorage
        builder = MonthlySnapshotBuilder()
        snap = builder.build(self._loans_df())
        storage = ZeroCostStorage(base_dir=tmp_path / 'duckdb', db_path=None)
        tables = builder.to_star_schema(snap, storage)
        assert 'dim_loan' in tables
        assert 'dim_time' in tables
        assert 'fact_monthly_snapshot' in tables
        assert len(tables['fact_monthly_snapshot']) == 4
