from __future__ import annotations
import math
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

class TestLoanTapeLoader:

    def _make_loan_csv(self, tmp_path: Path) -> Path:
        content = 'Loan ID,Disbursement Date,Disbursement Amount,Interest Rate,Term Months,Currency,Product Type,Branch Code,Customer ID\nL-001,2025-01-15,10000,0.24,12,USD,microcredito,BR01,C-001\nL-002,2025-03-01,20000,0.22,24,USD,microcredito,BR02,C-002\n'
        p = tmp_path / 'loan_data.csv'
        p.write_text(content)
        return p

    def _make_schedule_csv(self, tmp_path: Path) -> Path:
        content = 'Loan ID,Payment Date,Principal,Interest,Fee,Total,Installment Number\nL-001,2025-02-15,800,20,5,825,1\nL-001,2025-03-15,800,18,5,823,2\nL-002,2025-04-01,800,37,5,842,1\n'
        p = tmp_path / 'payment_schedule.csv'
        p.write_text(content)
        return p

    def _make_payment_csv(self, tmp_path: Path) -> Path:
        content = 'Loan ID,True Payment Date,True Total,True Principal Payment,True Interest Payment,True Fee Payment\nL-001,2025-02-15,825,800,20,5\nL-001,2025-03-15,823,800,18,5\n'
        p = tmp_path / 'real_payment.csv'
        p.write_text(content)
        return p

    def test_load_all_returns_required_tables(self, tmp_path):
        from backend.src.zero_cost.loan_tape_loader import LoanTapeLoader
        self._make_loan_csv(tmp_path)
        self._make_schedule_csv(tmp_path)
        self._make_payment_csv(tmp_path)
        loader = LoanTapeLoader(data_dir=tmp_path)
        tables = loader.load_all()
        assert 'dim_loan' in tables
        assert 'fact_schedule' in tables
        assert 'fact_real_payment' in tables

    def test_dim_loan_has_loan_id_key(self, tmp_path):
        from backend.src.zero_cost.loan_tape_loader import LoanTapeLoader
        self._make_loan_csv(tmp_path)
        self._make_schedule_csv(tmp_path)
        self._make_payment_csv(tmp_path)
        loader = LoanTapeLoader(data_dir=tmp_path)
        tables = loader.load_all()
        assert 'loan_id' in tables['dim_loan'].columns
        assert len(tables['dim_loan']) == 2

    def test_fact_schedule_has_loan_id(self, tmp_path):
        from backend.src.zero_cost.loan_tape_loader import LoanTapeLoader
        self._make_loan_csv(tmp_path)
        self._make_schedule_csv(tmp_path)
        self._make_payment_csv(tmp_path)
        loader = LoanTapeLoader(data_dir=tmp_path)
        tables = loader.load_all()
        assert 'loan_id' in tables['fact_schedule'].columns
        assert 'scheduled_principal' in tables['fact_schedule'].columns

    def test_fact_real_payment_has_loan_id(self, tmp_path):
        from backend.src.zero_cost.loan_tape_loader import LoanTapeLoader
        self._make_loan_csv(tmp_path)
        self._make_schedule_csv(tmp_path)
        self._make_payment_csv(tmp_path)
        loader = LoanTapeLoader(data_dir=tmp_path)
        tables = loader.load_all()
        assert 'loan_id' in tables['fact_real_payment'].columns
        assert 'paid_principal' in tables['fact_real_payment'].columns

    def test_source_tag_is_set(self, tmp_path):
        from backend.src.zero_cost.loan_tape_loader import LoanTapeLoader
        self._make_loan_csv(tmp_path)
        self._make_schedule_csv(tmp_path)
        self._make_payment_csv(tmp_path)
        loader = LoanTapeLoader(source_tag='loan_tape', data_dir=tmp_path)
        tables = loader.load_all()
        assert (tables['dim_loan']['source'] == 'loan_tape').all()

    def test_control_mora_and_loan_tape_share_loan_id_column(self, tmp_path):
        from backend.src.zero_cost.control_mora_adapter import ControlMoraAdapter
        from backend.src.zero_cost.loan_tape_loader import LoanTapeLoader
        self._make_loan_csv(tmp_path)
        self._make_schedule_csv(tmp_path)
        self._make_payment_csv(tmp_path)
        loader = LoanTapeLoader(data_dir=tmp_path)
        tape_tables = loader.load_all()
        mora_content = 'NumeroDesembolso,lend_id,NombreCliente,SaldoVigente,TotalVencido,DPD,FechaDesembolso\nNDE-001,L-001,Juan Perez,10000,0,0,2025-01-15\n'
        mora_path = tmp_path / 'control_mora.csv'
        mora_path.write_text(mora_content)
        adapter = ControlMoraAdapter(snapshot_month='2026-02-28')
        mora_df = adapter.load(mora_path)
        assert 'loan_id' in tape_tables['dim_loan'].columns
        assert 'lend_id' in mora_df.columns or 'loan_id' in mora_df.columns

class TestCrosswalk:

    def _make_tape_df(self) -> pd.DataFrame:
        return pd.DataFrame({'loan_id': ['L-001', 'L-002', 'L-003'], 'client_name': ['Juan Perez', 'Maria Lopez', 'No Match Person'], 'disbursement_date': pd.to_datetime(['2025-01-15', '2025-03-01', '2025-05-10']), 'original_principal': [10000, 20000, 5000]})

    def _make_mora_df(self) -> pd.DataFrame:
        return pd.DataFrame({'lend_id': ['L-001', 'L-002'], 'numero_desembolso': ['NDE-001', 'NDE-002'], 'client_name': ['Juan Pérez', 'Maria Lopez G.'], 'disbursement_date': pd.to_datetime(['2025-01-15', '2025-03-01'])})

    def test_unmatched_file_is_created(self, tmp_path):
        from backend.src.zero_cost.crosswalk import Crosswalk
        cw = Crosswalk()
        cw.build(self._make_tape_df(), self._make_mora_df())
        out = tmp_path / 'unmatched_records.csv'
        cw.export_unmatched(out)
        assert out.exists()

    def test_unmatched_reason_code_not_empty(self, tmp_path):
        from backend.src.zero_cost.crosswalk import Crosswalk
        cw = Crosswalk()
        cw.build(self._make_tape_df(), self._make_mora_df())
        out = tmp_path / 'unmatched_records.csv'
        cw.export_unmatched(out)
        df = pd.read_csv(out)
        assert len(df) > 0, 'Expected at least one unmatched record (L-003)'
        assert not df['reason_code'].isna().any(), 'reason_code must not be empty'
        assert (df['reason_code'] != '').all(), 'reason_code must not be blank'

    def test_exact_match_resolves(self):
        from backend.src.zero_cost.crosswalk import Crosswalk
        cw = Crosswalk()
        cw.build(self._make_tape_df(), self._make_mora_df())
        assert cw.to_operation_id('L-001') == 'L-001'

    def test_unmatched_file_exists_even_when_all_matched(self, tmp_path):
        from backend.src.zero_cost.crosswalk import Crosswalk
        tape = pd.DataFrame({'loan_id': ['L-001']})
        mora = pd.DataFrame({'lend_id': ['L-001'], 'numero_desembolso': ['NDE-001']})
        cw = Crosswalk()
        cw.build(tape, mora)
        out = tmp_path / 'unmatched.csv'
        cw.export_unmatched(out)
        assert out.exists()

class TestXIRR:

    def test_simple_known_case(self):
        from backend.src.zero_cost.xirr import xirr
        cashflows = [-1000.0, 1200.0]
        dates = ['2025-01-01', '2026-01-01']
        rate = xirr(cashflows, dates)
        assert abs(rate - 0.2) < 0.001, f'Expected ~0.20, got {rate}'

    def test_realistic_loan_cashflows(self):
        from backend.src.zero_cost.xirr import xirr
        cashflows = [-10000, 950, 950, 950, 950, 950, 950, 950, 950, 950, 1750]
        dates = pd.date_range('2025-01-31', periods=11, freq='ME').tolist()
        rate = xirr(cashflows, dates)
        assert math.isfinite(rate), f'XIRR should converge, got {rate}'
        assert rate > 0, f'Rate should be positive, got {rate}'

    def test_all_negative_raises_value_error(self):
        from backend.src.zero_cost.xirr import xirr
        with pytest.raises(ValueError, match='at least one positive'):
            xirr([-1000.0, -500.0], ['2025-01-01', '2026-01-01'])

    def test_all_positive_raises_value_error(self):
        from backend.src.zero_cost.xirr import xirr
        with pytest.raises(ValueError, match='at least one positive'):
            xirr([1000.0, 500.0], ['2025-01-01', '2026-01-01'])

    def test_mismatched_lengths_raises_value_error(self):
        from backend.src.zero_cost.xirr import xirr
        with pytest.raises(ValueError):
            xirr([-1000, 500], ['2025-01-01'])

    def test_irregular_dates(self):
        from backend.src.zero_cost.xirr import xirr
        cashflows = [-5000, 1000, 1500, 3000]
        dates = ['2025-01-01', '2025-04-15', '2025-09-30', '2026-02-01']
        rate = xirr(cashflows, dates)
        assert math.isfinite(rate), 'XIRR should converge for valid flows'

    def test_cashflows_order_independent(self):
        from backend.src.zero_cost.xirr import xirr
        cashflows = [-1000.0, 1200.0]
        dates_forward = ['2025-01-01', '2026-01-01']
        dates_reversed = ['2026-01-01', '2025-01-01']
        cashflows_reversed = [1200.0, -1000.0]
        rate_fwd = xirr(cashflows, dates_forward)
        rate_rev = xirr(cashflows_reversed, dates_reversed)
        assert abs(rate_fwd - rate_rev) < 1e-06, f'Rate should be order-independent: {rate_fwd} vs {rate_rev}'

    def test_contractual_apr_monthly_compounding(self):
        from backend.src.zero_cost.xirr import contractual_apr
        ear = contractual_apr(0.24, payments_per_year=12)
        assert abs(ear - 0.2682) < 0.001, f'Expected ~0.2682, got {ear}'

    def test_contractual_apr_annual(self):
        from backend.src.zero_cost.xirr import contractual_apr
        ear = contractual_apr(0.15, payments_per_year=1)
        assert abs(ear - 0.15) < 1e-09

    def test_loan_xirr_returns_float(self):
        from backend.src.zero_cost.xirr import loan_xirr
        disb = pd.DataFrame({'loan_id': ['L-001'], 'disbursement_date': pd.to_datetime(['2025-01-01']), 'original_principal': [10000.0]})
        pays = pd.DataFrame({'loan_id': ['L-001', 'L-001', 'L-001'], 'payment_date': pd.to_datetime(['2025-04-01', '2025-07-01', '2026-01-01']), 'paid_total': [3000.0, 3000.0, 5000.0]})
        rate = loan_xirr(disb, pays, 'L-001')
        assert math.isfinite(rate), f'Expected finite rate, got {rate}'
        assert rate > 0

    def test_loan_xirr_missing_loan_returns_nan(self):
        from backend.src.zero_cost.xirr import loan_xirr
        disb = pd.DataFrame({'loan_id': ['L-001'], 'disbursement_date': ['2025-01-01'], 'original_principal': [1000.0]})
        pays = pd.DataFrame({'loan_id': [], 'payment_date': [], 'paid_total': []})
        rate = loan_xirr(disb, pays, 'NONEXISTENT')
        assert math.isnan(rate)

    def test_portfolio_xirr_returns_series(self):
        from backend.src.zero_cost.xirr import portfolio_xirr
        disb = pd.DataFrame({'loan_id': ['L-001', 'L-002'], 'disbursement_date': pd.to_datetime(['2025-01-01', '2025-06-01']), 'original_principal': [10000.0, 5000.0]})
        pays = pd.DataFrame({'loan_id': ['L-001', 'L-001', 'L-002'], 'payment_date': pd.to_datetime(['2025-07-01', '2026-01-01', '2026-06-01']), 'paid_total': [5000.0, 6000.0, 6000.0]})
        result = portfolio_xirr(disb, pays)
        assert isinstance(result, pd.Series)
        assert set(result.index) == {'L-001', 'L-002'}

class TestPipelineRouter:

    def test_jan_2026_uses_loan_tape(self):
        from backend.src.zero_cost.pipeline_router import PipelineRouter
        router = PipelineRouter()
        assert router.source_for('2026-01-31') == 'loan_tape'

    def test_dec_2025_uses_loan_tape(self):
        from backend.src.zero_cost.pipeline_router import PipelineRouter
        router = PipelineRouter()
        assert router.source_for('2025-12-31') == 'loan_tape'

    def test_feb_2026_uses_control_mora(self):
        from backend.src.zero_cost.pipeline_router import PipelineRouter
        router = PipelineRouter()
        assert router.source_for('2026-02-28') == 'control_mora'

    def test_march_2026_uses_control_mora(self):
        from backend.src.zero_cost.pipeline_router import PipelineRouter
        router = PipelineRouter()
        assert router.source_for('2026-03-31') == 'control_mora'

    def test_custom_pivot_month(self):
        from backend.src.zero_cost.pipeline_router import PipelineRouter
        router = PipelineRouter(pivot_month='2025-06-01')
        assert router.source_for('2025-05-31') == 'loan_tape'
        assert router.source_for('2025-06-30') == 'control_mora'

class TestExporter:

    def _sample_df(self) -> pd.DataFrame:
        return pd.DataFrame({'loan_id': ['L-001', 'L-002'], 'snapshot_month': pd.to_datetime(['2026-01-31', '2026-01-31']), 'outstanding_principal': [9000.0, 18000.0]})

    def test_parquet_file_is_created(self, tmp_path):
        from backend.src.zero_cost.exporter import Exporter
        exp = Exporter(output_dir=tmp_path)
        exp.export_snapshot(self._sample_df())
        assert (tmp_path / 'fact_monthly_snapshot.parquet').exists()

    def test_csv_file_is_created(self, tmp_path):
        from backend.src.zero_cost.exporter import Exporter
        exp = Exporter(output_dir=tmp_path, write_csv=True)
        exp.export_snapshot(self._sample_df())
        assert (tmp_path / 'fact_monthly_snapshot.csv').exists()

    def test_export_tables_writes_multiple_files(self, tmp_path):
        from backend.src.zero_cost.exporter import Exporter
        exp = Exporter(output_dir=tmp_path)
        tables = {'dim_loan': self._sample_df(), 'fact_schedule': self._sample_df(), '_source': 'loan_tape'}
        exp.export_tables(tables)
        assert (tmp_path / 'dim_loan.parquet').exists()
        assert (tmp_path / 'fact_schedule.parquet').exists()
        assert not (tmp_path / '_source.parquet').exists()

    def test_unmatched_records_file_exists(self, tmp_path):
        from backend.src.zero_cost.exporter import Exporter
        exp = Exporter(output_dir=tmp_path)
        unmatched = pd.DataFrame({'loan_id': ['L-999'], 'operation_id': [None], 'match_type': ['unmatched'], 'reason_code': ['unmatched_loan_tape']})
        exp.export_unmatched(unmatched)
        path = tmp_path / 'unmatched_records.csv'
        assert path.exists()
        df = pd.read_csv(path)
        assert not df['reason_code'].isna().any()
        assert (df['reason_code'] != '').all()

    def test_manifest_is_written(self, tmp_path):
        import json
        from backend.src.zero_cost.exporter import Exporter
        exp = Exporter(output_dir=tmp_path)
        exp.export_snapshot(self._sample_df())
        exp.write_manifest(snapshot_month='2026-01-31', source='loan_tape')
        manifest_path = tmp_path / 'run_manifest.json'
        assert manifest_path.exists()
        content = json.loads(manifest_path.read_text())
        assert 'generated_at' in content
        assert content['snapshot_month'] == '2026-01-31'

class TestDPDCalculator:

    def _make_inputs(self):
        dim_loan = pd.DataFrame({'loan_id': ['L-001', 'L-002'], 'original_principal': [10000.0, 5000.0]})
        fact_schedule = pd.DataFrame({'loan_id': ['L-001', 'L-001', 'L-002'], 'scheduled_date': pd.to_datetime(['2026-01-31', '2026-02-28', '2026-01-31']), 'scheduled_principal': [1000.0, 1000.0, 1000.0]})
        fact_real_payment = pd.DataFrame({'loan_id': ['L-001', 'L-002'], 'payment_date': pd.to_datetime(['2026-01-31', '2026-01-31']), 'paid_principal': [1000.0, 1000.0]})
        return (dim_loan, fact_schedule, fact_real_payment)

    def test_build_snapshots_returns_dataframe(self):
        from backend.python.kpis.dpd_calculator import DPDCalculator
        calc = DPDCalculator()
        dim_loan, sched, pays = self._make_inputs()
        snap = calc.build_snapshots(dim_loan, sched, pays, ['2026-02-28'])
        assert isinstance(snap, pd.DataFrame)
        assert len(snap) == 2

    def test_current_loan_has_zero_dpd(self):
        from backend.python.kpis.dpd_calculator import DPDCalculator
        calc = DPDCalculator()
        dim_loan, sched, pays = self._make_inputs()
        snap = calc.build_snapshots(dim_loan, sched, pays, ['2026-01-31'])
        l2_row = snap[snap['loan_id'] == 'L-002'].iloc[0]
        assert l2_row['dpd'] == 0

    def test_overdue_loan_has_positive_dpd(self):
        from backend.python.kpis.dpd_calculator import DPDCalculator
        calc = DPDCalculator()
        dim_loan, sched, pays = self._make_inputs()
        snap = calc.build_snapshots(dim_loan, sched, pays, ['2026-03-15'])
        l1_row = snap[snap['loan_id'] == 'L-001'].iloc[0]
        assert l1_row['dpd'] > 0

    def test_par_flags_set_correctly(self):
        from backend.python.kpis.dpd_calculator import DPDCalculator
        calc = DPDCalculator(par_thresholds=[1, 30])
        dim_loan, sched, pays = self._make_inputs()
        snap = calc.build_snapshots(dim_loan, sched, pays, ['2026-03-15'])
        l1_row = snap[snap['loan_id'] == 'L-001'].iloc[0]
        l2_row = snap[snap['loan_id'] == 'L-002'].iloc[0]
        assert l1_row['par_1']
        assert not l1_row['par_30']
        assert not l2_row['par_1']

    def test_mora_bucket_is_populated(self):
        from backend.python.kpis.dpd_calculator import DPDCalculator
        calc = DPDCalculator()
        dim_loan, sched, pays = self._make_inputs()
        snap = calc.build_snapshots(dim_loan, sched, pays, ['2026-02-28'])
        assert 'mora_bucket' in snap.columns
        assert snap['mora_bucket'].notna().all()
