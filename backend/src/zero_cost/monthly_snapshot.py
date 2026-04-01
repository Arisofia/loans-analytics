from __future__ import annotations
import logging
from datetime import date
from decimal import Decimal
import pandas as pd
from backend.python.kpis.dpd_calculator import dpd_to_bucket
from .storage import ZeroCostStorage
logger = logging.getLogger(__name__)

class MonthlySnapshotBuilder:

    def __init__(self, par_thresholds: list[int] | None=None, currency_col: str='currency') -> None:
        self.par_thresholds = par_thresholds or [1, 30, 60, 90]
        self.currency_col = currency_col

    def build(self, loans_df: pd.DataFrame, as_of_month: str | date | None=None, payments_df: pd.DataFrame | None=None) -> pd.DataFrame:
        df = loans_df.copy()
        df = self._set_snapshot_month(df, as_of_month)
        if 'lend_id' not in df.columns and 'numero_desembolso' in df.columns:
            df['lend_id'] = df['numero_desembolso']
        if 'dpd' in df.columns:
            df['mora_bucket'] = df['dpd'].apply(dpd_to_bucket)
        elif 'mora_bucket' not in df.columns:
            df['mora_bucket'] = 'unknown'
        if 'dpd' in df.columns:
            df['is_overdue'] = df['dpd'].fillna(0) > 0
        for threshold in self.par_thresholds:
            col = f'par_{threshold}'
            if 'dpd' in df.columns:
                df[col] = df['dpd'].fillna(0) >= threshold
        if payments_df is not None:
            df = self._join_monthly_income(df, payments_df)
        if 'disbursement_date' in df.columns:
            snap_dates = pd.to_datetime(df['snapshot_month'], format='mixed')
            disb_dates = pd.to_datetime(df['disbursement_date'], format='mixed')
            df['months_on_book'] = ((snap_dates.dt.year - disb_dates.dt.year) * 12 + (snap_dates.dt.month - disb_dates.dt.month)).clip(lower=0)
        logger.info('MonthlySnapshotBuilder: built %d snapshot rows for %s', len(df), df['snapshot_month'].iloc[0] if len(df) > 0 else 'n/a')
        return df

    def to_star_schema(self, snapshot_df: pd.DataFrame, storage: ZeroCostStorage) -> dict[str, pd.DataFrame]:
        tables: dict[str, pd.DataFrame] = {}
        loan_cols = [c for c in ['lend_id', 'numero_desembolso', 'product_type', 'branch_code', 'currency', 'disbursement_date'] if c in snapshot_df.columns]
        if loan_cols:
            dim_loan = snapshot_df[loan_cols].drop_duplicates(subset=['lend_id'] if 'lend_id' in loan_cols else loan_cols[:1]).reset_index(drop=True)
            dim_loan['loan_sk'] = range(1, len(dim_loan) + 1)
            tables['dim_loan'] = dim_loan
        client_cols = [c for c in ['lend_id', 'client_id', 'client_name'] if c in snapshot_df.columns]
        if len(client_cols) > 1:
            dim_client = snapshot_df[client_cols].drop_duplicates().reset_index(drop=True)
            dim_client['client_sk'] = range(1, len(dim_client) + 1)
            tables['dim_client'] = dim_client
        if 'snapshot_month' in snapshot_df.columns:
            time_df = snapshot_df[['snapshot_month']].drop_duplicates().copy()
            time_df['snapshot_month'] = pd.to_datetime(time_df['snapshot_month'], format='mixed')
            time_df['year'] = time_df['snapshot_month'].dt.year
            time_df['month'] = time_df['snapshot_month'].dt.month
            time_df['quarter'] = time_df['snapshot_month'].dt.quarter
            time_df['year_month'] = time_df['snapshot_month'].dt.strftime('%Y-%m')
            time_df = time_df.reset_index(drop=True)
            time_df['time_id'] = range(1, len(time_df) + 1)
            tables['dim_time'] = time_df
        fact_df = snapshot_df.copy()
        if 'dim_loan' in tables and 'lend_id' in fact_df.columns:
            fact_df = fact_df.merge(tables['dim_loan'][['lend_id', 'loan_sk']], on='lend_id', how='left')
        if 'dim_client' in tables:
            dim_client = tables['dim_client']
            join_keys = [c for c in ['lend_id', 'client_id'] if c in fact_df.columns and c in dim_client.columns]
            if join_keys:
                fact_df = fact_df.merge(dim_client[join_keys + ['client_sk']], on=join_keys, how='left')
        if 'dim_time' in tables and 'snapshot_month' in fact_df.columns:
            fact_df = fact_df.merge(tables['dim_time'][['snapshot_month', 'time_id']], on='snapshot_month', how='left')
        tables['fact_monthly_snapshot'] = fact_df.reset_index(drop=True)
        for name, table_df in tables.items():
            storage.write_parquet(table_df, name)
            logger.info('Wrote %s (%d rows)', name, len(table_df))
        return tables

    def compute_portfolio_kpis(self, snapshot_df: pd.DataFrame) -> dict:
        kpis: dict = {}
        kpis['total_loans'] = len(snapshot_df)
        if 'principal_outstanding' in snapshot_df.columns:
            total_os_raw = snapshot_df['principal_outstanding'].sum()
            if pd.notna(total_os_raw):
                total_os = Decimal(str(total_os_raw))
                kpis['total_outstanding'] = float(total_os)
            else:
                total_os = Decimal('0')
                kpis['total_outstanding'] = 0.0
        else:
            total_os = Decimal('0')
            kpis['total_outstanding'] = 0.0
        if 'principal_outstanding' in snapshot_df.columns:
            active_mask = snapshot_df['principal_outstanding'] > 0
            kpis['active_loans'] = int(active_mask.sum())
        else:
            kpis['active_loans'] = kpis['total_loans']
        if 'total_overdue_amount' in snapshot_df.columns:
            total_overdue_raw = snapshot_df['total_overdue_amount'].sum()
            if pd.notna(total_overdue_raw):
                total_overdue = Decimal(str(total_overdue_raw))
                kpis['total_overdue'] = float(total_overdue)
            else:
                kpis['total_overdue'] = 0.0
        else:
            kpis['total_overdue'] = 0.0
        for threshold in self.par_thresholds:
            par_col = f'par_{threshold}'
            if par_col in snapshot_df.columns and total_os > Decimal('0'):
                par_amount_raw = snapshot_df.loc[snapshot_df[par_col], 'principal_outstanding'].sum()
                if pd.notna(par_amount_raw):
                    par_amount = Decimal(str(par_amount_raw))
                    par_pct = par_amount / total_os * Decimal('100')
                    par_value = float(par_pct)
                    kpis[f'par_{threshold}_pct'] = par_value
                    kpis[f'par_{threshold}'] = par_value
        if 'dpd' in snapshot_df.columns:
            kpis['avg_dpd'] = float(snapshot_df['dpd'].mean())
            if 'principal_outstanding' in snapshot_df.columns and snapshot_df['principal_outstanding'].notna().any():
                weights = snapshot_df['principal_outstanding']
                total_weight = weights.sum()
                if pd.notna(total_weight) and float(total_weight) > 0.0:
                    weighted_sum = (snapshot_df['dpd'] * weights).sum()
                    weighted_avg_dpd = float(weighted_sum / total_weight)
                    kpis['weighted_avg_dpd'] = weighted_avg_dpd
        if 'mora_bucket' in snapshot_df.columns:
            kpis['mora_distribution'] = snapshot_df['mora_bucket'].value_counts().to_dict()
        return kpis

    def _set_snapshot_month(self, df: pd.DataFrame, as_of_month: str | date | None) -> pd.DataFrame:
        if as_of_month is not None:
            raw = pd.to_datetime(str(as_of_month), format='mixed')
            df['snapshot_month'] = (raw + pd.offsets.MonthEnd(0)).normalize()
        elif 'snapshot_month' not in df.columns:
            today = pd.Timestamp('today').normalize()
            current_month_end = today + pd.offsets.MonthEnd(0)
            df['snapshot_month'] = current_month_end
            logger.warning('snapshot_month not provided — defaulting to current month-end %s', current_month_end.date())
        else:
            df['snapshot_month'] = pd.to_datetime(df['snapshot_month'], errors='coerce', format='mixed') + pd.offsets.MonthEnd(0)
        return df

    def _join_monthly_income(self, df: pd.DataFrame, payments_df: pd.DataFrame) -> pd.DataFrame:
        if 'lend_id' not in payments_df.columns or 'amount' not in payments_df.columns:
            return df
        monthly_income = payments_df.groupby('lend_id')['amount'].sum().rename('monthly_income').reset_index()
        return df.merge(monthly_income, on='lend_id', how='left')
