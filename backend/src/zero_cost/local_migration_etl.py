from __future__ import annotations
import argparse
import csv
import logging
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from backend.python.kpis.dpd_calculator import DPDCalculator
from .loan_tape_loader import LoanTapeLoader
from .xirr import contractual_apr, portfolio_xirr
logger = logging.getLogger(__name__)
NOT_SPECIFIED_VALUES = {'no especificado', 'no_especificado', 'not specified', ''}
MAX_NOT_SPECIFIED_LOG_ROWS = 10000

@dataclass
class ETLResult:
    dim_loan: pd.DataFrame
    fact_schedule: pd.DataFrame
    fact_real_payment: pd.DataFrame
    fact_monthly_snapshot: pd.DataFrame
    payment_reconciliation: pd.DataFrame
    unmatched_records: pd.DataFrame

def _normalize_not_specified(value: object) -> bool:
    if value is None or pd.isna(value):
        return True
    return str(value).strip().lower() in NOT_SPECIFIED_VALUES

def _not_specified_mask(series: pd.Series) -> pd.Series:
    na_mask = series.isna()
    s_str = series.astype('string')
    s_norm = s_str.str.strip().str.lower()
    value_mask = s_norm.isin(NOT_SPECIFIED_VALUES)
    return na_mask | value_mask

def build_not_specified_log(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    _EMPTY_COLS = ['table_name', 'record_ref', 'field_name', 'reason_code', 'reason_detail']
    if df.empty or df.columns.empty:
        return pd.DataFrame(columns=_EMPTY_COLS)
    mask_series: list[pd.Series] = []
    detail_suffix_by_col: dict[str, str] = {}
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            mask = _not_specified_mask(df[col])
            detail_suffix_by_col[col] = 'no especificado/blank value'
        else:
            mask = df[col].isna()
            detail_suffix_by_col[col] = 'null/NaT value'
        if mask.any():
            mask_series.append(mask.rename(col))
    if not mask_series:
        return pd.DataFrame(columns=_EMPTY_COLS)
    flagged_idx = pd.concat(mask_series, axis=1).stack()
    flagged_idx = flagged_idx[flagged_idx].index
    if len(flagged_idx) == 0:
        return pd.DataFrame(columns=_EMPTY_COLS)
    if len(flagged_idx) > MAX_NOT_SPECIFIED_LOG_ROWS:
        logger.warning("Truncated not-specified log for table '%s' after %d records to keep ETL artifacts bounded.", table_name, MAX_NOT_SPECIFIED_LOG_ROWS)
        flagged_idx = flagged_idx[:MAX_NOT_SPECIFIED_LOG_ROWS]
    row_refs = [str(r) for r, _ in flagged_idx]
    col_names = [c for _, c in flagged_idx]
    detail_suffixes = [detail_suffix_by_col[c] for c in col_names]
    return pd.DataFrame({'table_name': table_name, 'record_ref': row_refs, 'field_name': col_names, 'reason_code': 'not_specified', 'reason_detail': [f"Field '{c}' is not specified / {d}" for c, d in zip(col_names, detail_suffixes)]})

def reconcile_payments(fact_schedule: pd.DataFrame, fact_real_payment: pd.DataFrame, *, tolerance: float=0.01) -> tuple[pd.DataFrame, pd.DataFrame]:
    schedule = fact_schedule.copy()
    paid = fact_real_payment.copy()
    schedule['scheduled_date'] = pd.to_datetime(schedule['scheduled_date'], errors='coerce')
    paid['payment_date'] = pd.to_datetime(paid['payment_date'], errors='coerce')
    schedule['scheduled_total'] = pd.to_numeric(schedule['scheduled_total'], errors='coerce').fillna(0.0)
    paid['paid_total'] = pd.to_numeric(paid['paid_total'], errors='coerce').fillna(0.0)
    excluded_rows_unmatched: list[pd.DataFrame] = []
    sched_invalid = schedule[schedule['scheduled_date'].isna()].copy()
    if not sched_invalid.empty:
        sched_invalid = sched_invalid.assign(status='invalid_date', reason_code='invalid_scheduled_date', reason_detail='loan_id=' + sched_invalid['loan_id'].astype(str) + ', scheduled_total=' + sched_invalid['scheduled_total'].round(2).astype(str))
        excluded_rows_unmatched.append(sched_invalid[['loan_id', 'reason_code', 'reason_detail', 'status']])
    paid_invalid = paid[paid['payment_date'].isna()].copy()
    if not paid_invalid.empty:
        paid_invalid = paid_invalid.assign(status='invalid_date', reason_code='invalid_payment_date', reason_detail='loan_id=' + paid_invalid['loan_id'].astype(str) + ', paid_total=' + paid_invalid['paid_total'].round(2).astype(str))
        excluded_rows_unmatched.append(paid_invalid[['loan_id', 'reason_code', 'reason_detail', 'status']])
    sched_missing_loan = schedule[schedule['loan_id'].isna() & schedule['scheduled_date'].notna()].copy()
    if not sched_missing_loan.empty:
        sched_missing_loan = sched_missing_loan.assign(status='invalid_key', reason_code='missing_loan_id_schedule', reason_detail='loan_id=NaN, scheduled_date=' + sched_missing_loan['scheduled_date'].astype(str) + ', scheduled_total=' + sched_missing_loan['scheduled_total'].round(2).astype(str))
        excluded_rows_unmatched.append(sched_missing_loan[['loan_id', 'reason_code', 'reason_detail', 'status']])
    paid_missing_loan = paid[paid['loan_id'].isna() & paid['payment_date'].notna()].copy()
    if not paid_missing_loan.empty:
        paid_missing_loan = paid_missing_loan.assign(status='invalid_key', reason_code='missing_loan_id_payment', reason_detail='loan_id=NaN, payment_date=' + paid_missing_loan['payment_date'].astype(str) + ', paid_total=' + paid_missing_loan['paid_total'].round(2).astype(str))
        excluded_rows_unmatched.append(paid_missing_loan[['loan_id', 'reason_code', 'reason_detail', 'status']])
    sched_agg = schedule.dropna(subset=['scheduled_date', 'loan_id']).groupby(['loan_id', 'scheduled_date'], as_index=False)['scheduled_total'].sum()
    paid_agg = paid.dropna(subset=['payment_date', 'loan_id']).groupby(['loan_id', 'payment_date'], as_index=False)['paid_total'].sum()
    merged = sched_agg.merge(paid_agg, how='outer', left_on=['loan_id', 'scheduled_date'], right_on=['loan_id', 'payment_date'], indicator=True)
    merged['scheduled_total'] = merged['scheduled_total'].fillna(0.0)
    merged['paid_total'] = merged['paid_total'].fillna(0.0)
    merged['amount_diff'] = merged['paid_total'] - merged['scheduled_total']
    merged['status'] = 'reconciled'
    merged.loc[merged['_merge'] == 'left_only', 'status'] = 'missing_payment'
    merged.loc[merged['_merge'] == 'right_only', 'status'] = 'missing_schedule'
    amount_mismatch = (merged['_merge'] == 'both') & (merged['amount_diff'].abs() > tolerance)
    merged.loc[amount_mismatch, 'status'] = 'amount_mismatch'
    status_to_reason = {'missing_payment': 'scheduled_without_payment', 'missing_schedule': 'payment_without_schedule', 'amount_mismatch': 'amount_mismatch'}
    unmatched = merged[merged['status'] != 'reconciled'].copy()
    unmatched['reason_code'] = unmatched['status'].map(status_to_reason).fillna('not_specified')
    unmatched['reason_detail'] = 'loan_id=' + unmatched['loan_id'].astype(str) + ', amount_diff=' + unmatched['amount_diff'].round(2).astype(str)
    if excluded_rows_unmatched:
        unmatched = pd.concat([unmatched, *excluded_rows_unmatched], ignore_index=True)
    return (merged.drop(columns=['_merge']), unmatched)

class LocalMonthlySnapshotETL:

    def __init__(self, snapshot_month: str) -> None:
        self.snapshot_month = pd.Timestamp(snapshot_month) + pd.offsets.MonthEnd(0)
        self.loader = LoanTapeLoader(data_dir='data/raw')
        self.dpd_calculator = DPDCalculator()

    def run(self, *, loan_tape_dir: str | Path, control_mora_path: str | Path | None=None) -> ETLResult:
        tables = self.loader.load_all(data_dir=loan_tape_dir)
        dim_loan = tables['dim_loan'].copy()
        fact_schedule = tables['fact_schedule'].copy()
        fact_real_payment = tables['fact_real_payment'].copy()
        dim_loan['disbursement_date'] = pd.to_datetime(dim_loan['disbursement_date'], errors='coerce')
        dim_loan['original_principal'] = pd.to_numeric(dim_loan['original_principal'], errors='coerce').fillna(0.0)
        if 'interest_rate' not in dim_loan.columns:
            dim_loan['interest_rate'] = 0.0
        else:
            dim_loan['interest_rate'] = pd.to_numeric(dim_loan['interest_rate'], errors='coerce').fillna(0.0)
        snapshots = self.dpd_calculator.build_snapshots(dim_loan, fact_schedule, fact_real_payment, month_ends=[self.snapshot_month])
        dim_loan['contractual_apr'] = dim_loan['interest_rate'].apply(contractual_apr)
        xirr_eligible = dim_loan[dim_loan['disbursement_date'].notna() & (dim_loan['original_principal'] > 0)]
        loan_xirr_series = portfolio_xirr(xirr_eligible, fact_real_payment)
        fact_monthly_snapshot = snapshots.merge(dim_loan[['loan_id', 'contractual_apr']], on='loan_id', how='left')
        fact_monthly_snapshot = fact_monthly_snapshot.merge(loan_xirr_series.rename('realized_xirr'), left_on='loan_id', right_index=True, how='left')
        reconciliation, unmatched_reconciliation = reconcile_payments(fact_schedule, fact_real_payment)
        not_specified_logs = [build_not_specified_log(dim_loan, 'dim_loan'), build_not_specified_log(fact_schedule, 'fact_schedule'), build_not_specified_log(fact_real_payment, 'fact_real_payment')]
        unmatched_records = pd.concat([unmatched_reconciliation, *[df for df in not_specified_logs if not df.empty]], ignore_index=True)
        if control_mora_path:
            control_mora_path = Path(control_mora_path)
            with control_mora_path.open('r', encoding='utf-8-sig', newline='') as _f:
                _sample = _f.read(4096)
                _f.seek(0)
                try:
                    _dialect = csv.Sniffer().sniff(_sample, delimiters=',;\t|')
                    delimiter = _dialect.delimiter
                except csv.Error:
                    delimiter = ','
                control_mora_df = pd.read_csv(_f, dtype=str, sep=delimiter, low_memory=False)
            unmatched_records = pd.concat([unmatched_records, build_not_specified_log(control_mora_df, 'control_mora')], ignore_index=True)
        if 'reason_code' in unmatched_records.columns:
            unmatched_records['reason_code'] = unmatched_records['reason_code'].fillna('not_specified')
        logger.info('LocalMonthlySnapshotETL completed snapshot=%s loans=%d unmatched=%d', self.snapshot_month.date(), len(dim_loan), len(unmatched_records))
        return ETLResult(dim_loan=dim_loan, fact_schedule=fact_schedule, fact_real_payment=fact_real_payment, fact_monthly_snapshot=fact_monthly_snapshot, payment_reconciliation=reconciliation, unmatched_records=unmatched_records)

def _parse_args(argv: list[str] | None=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build monthly star schema snapshot from raw CSV files')
    parser.add_argument('--loan-tape-dir', default='data/raw', help='Directory with loan tape CSV files')
    parser.add_argument('--control-mora', default='', help='Optional control mora CSV path')
    parser.add_argument('--snapshot-month', required=True, help='Snapshot month YYYY-MM-DD')
    parser.add_argument('--output-dir', default='exports/local_star', help='Output directory')
    return parser.parse_args(argv)

def _write(df: pd.DataFrame, output_dir: Path, name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f'{name}.csv'
    parquet_path = output_dir / f'{name}.parquet'
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False)
    logger.info('Wrote %s (%d rows)', csv_path, len(df))

def main(argv: list[str] | None=None) -> None:
    args = _parse_args(argv)
    etl = LocalMonthlySnapshotETL(snapshot_month=args.snapshot_month)
    result = etl.run(loan_tape_dir=args.loan_tape_dir, control_mora_path=args.control_mora or None)
    out = Path(args.output_dir)
    _write(result.dim_loan, out, 'dim_loan')
    _write(result.fact_schedule, out, 'fact_schedule')
    _write(result.fact_real_payment, out, 'fact_real_payment')
    _write(result.fact_monthly_snapshot, out, 'fact_monthly_snapshot')
    _write(result.payment_reconciliation, out, 'payment_reconciliation')
    unmatched_path = out / 'unmatched_records.csv'
    result.unmatched_records.to_csv(unmatched_path, index=False)
    logger.info('Wrote %s (%d rows)', unmatched_path, len(result.unmatched_records))
    if 'reason_code' in result.unmatched_records.columns:
        invalid = result.unmatched_records['reason_code'].fillna('').str.strip().eq('').sum()
        if invalid:
            raise SystemExit(f'Invalid unmatched_records: {invalid} rows without reason_code')
if __name__ == '__main__':
    main()
