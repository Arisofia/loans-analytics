from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
logger = logging.getLogger(__name__)
_LOAN_ALIASES: dict[str, str] = {'loan id': 'loan_id', 'loanid': 'loan_id', 'loan_id': 'loan_id', 'lend_id': 'loan_id', 'numero_desembolso': 'loan_id', 'numerodesembolso': 'loan_id', 'disbursement date': 'disbursement_date', 'disbursementdate': 'disbursement_date', 'fecha_desembolso': 'disbursement_date', 'disbursement amount': 'original_principal', 'disbursementamount': 'original_principal', 'principal0': 'original_principal', 'monto_desembolso': 'original_principal', 'interest rate': 'interest_rate', 'interest rate apr': 'interest_rate', 'interestrate': 'interest_rate', 'tasa_interes': 'interest_rate', 'term': 'term_months', 'term months': 'term_months', 'plazo': 'term_months', 'plazo_meses': 'term_months', 'currency': 'currency', 'loan currency': 'currency', 'moneda': 'currency', 'product type': 'product_type', 'producttype': 'product_type', 'tipo_producto': 'product_type', 'branch code': 'branch_code', 'branchcode': 'branch_code', 'sucursal': 'branch_code', 'customer id': 'client_id', 'customerid': 'client_id', 'client_id': 'client_id', 'id_cliente': 'client_id', 'maturity date': 'maturity_date', 'maturitydate': 'maturity_date', 'fecha_vencimiento': 'maturity_date', 'outstanding loan value': 'outstanding_loan_value'}
_SCHEDULE_ALIASES: dict[str, str] = {'loan id': 'loan_id', 'loanid': 'loan_id', 'loan_id': 'loan_id', 'payment date': 'scheduled_date', 'paymentdate': 'scheduled_date', 'fecha_pago': 'scheduled_date', 'total': 'scheduled_total', 'total payment': 'scheduled_total', 'totalpayment': 'scheduled_total', 'total_cuota': 'scheduled_total', 'principal': 'scheduled_principal', 'principal payment': 'scheduled_principal', 'principalpayment': 'scheduled_principal', 'principal_cuota': 'scheduled_principal', 'interest': 'scheduled_interest', 'interest payment': 'scheduled_interest', 'interestpayment': 'scheduled_interest', 'interes_cuota': 'scheduled_interest', 'fee': 'scheduled_fee', 'fee payment': 'scheduled_fee', 'feepayment': 'scheduled_fee', 'comision_cuota': 'scheduled_fee', 'other': 'scheduled_other', 'other payment': 'scheduled_other', 'installment number': 'installment_number', 'installmentnumber': 'installment_number', 'cuota_numero': 'installment_number'}
_REAL_PAYMENT_ALIASES: dict[str, str] = {'loan id': 'loan_id', 'loanid': 'loan_id', 'loan_id': 'loan_id', 'true payment date': 'payment_date', 'truepaymentdate': 'payment_date', 'fecha_pago_real': 'payment_date', 'payment date': 'payment_date', 'paymentdate': 'payment_date', 'true total': 'paid_total', 'truetotal': 'paid_total', 'true total payment': 'paid_total', 'truetotalpayment': 'paid_total', 'total_pagado': 'paid_total', 'true principal payment': 'paid_principal', 'trueprincipalpayment': 'paid_principal', 'capital_pagado': 'paid_principal', 'true interest payment': 'paid_interest', 'trueinterestpayment': 'paid_interest', 'interes_pagado': 'paid_interest', 'true fee payment': 'paid_fee', 'truefeepayment': 'paid_fee', 'comision_pagada': 'paid_fee', 'true other payment': 'paid_other', 'trueotherpayment': 'paid_other'}
_CUSTOMER_ALIASES: dict[str, str] = {'customer id': 'client_id', 'customerid': 'client_id', 'client_id': 'client_id', 'id_cliente': 'client_id', 'name': 'client_name', 'cliente': 'client_name', 'customer name': 'client_name', 'customername': 'client_name', 'nombre_cliente': 'client_name', 'identity number': 'identity_number', 'identitynumber': 'identity_number', 'cedula': 'identity_number', 'email': 'email', 'phone': 'phone', 'industry': 'industry', 'industria': 'industry', 'segment': 'segment', 'segmento': 'segment', 'kam': 'kam', 'account manager': 'kam', 'sales agent': 'kam'}
_COLLATERAL_ALIASES: dict[str, str] = {'loan id': 'loan_id', 'loanid': 'loan_id', 'loan_id': 'loan_id', 'collateral type': 'collateral_type', 'collateraltype': 'collateral_type', 'tipo_garantia': 'collateral_type', 'collateral value': 'collateral_value', 'collateral current': 'collateral_value', 'collateralvalue': 'collateral_value', 'valor_garantia': 'collateral_value', 'doc type': 'doc_type', 'doctype': 'doc_type', 'tipo_documento': 'doc_type'}
DIM_LOAN_COLUMNS = ['loan_id', 'client_id', 'disbursement_date', 'original_principal', 'interest_rate', 'term_months', 'currency', 'product_type', 'branch_code', 'maturity_date', 'source']
FACT_SCHEDULE_COLUMNS = ['loan_id', 'installment_number', 'scheduled_date', 'scheduled_total', 'scheduled_principal', 'scheduled_interest', 'scheduled_fee', 'scheduled_other']
FACT_REAL_PAYMENT_COLUMNS = ['loan_id', 'payment_date', 'paid_total', 'paid_principal', 'paid_interest', 'paid_fee', 'paid_other']
DIM_CUSTOMER_COLUMNS = ['client_id', 'client_name', 'identity_number', 'email', 'phone', 'industry', 'segment', 'kam']
DIM_COLLATERAL_COLUMNS = ['loan_id', 'collateral_type', 'collateral_value', 'doc_type']

def _slugify(col: str) -> str:
    import re
    return re.sub('[^a-z0-9 _]', '', col.strip().lower())

def _rename_cols(df: pd.DataFrame, alias_map: dict[str, str]) -> pd.DataFrame:
    mapping = {}
    for col in df.columns:
        canonical = alias_map.get(_slugify(col))
        if canonical:
            mapping[col] = canonical
    return df.rename(columns=mapping)

def _read_csv(path: Path, **kwargs) -> pd.DataFrame:
    raw = path.read_bytes()
    sep = ';' if b';' in raw[:2048] else ','
    return pd.read_csv(path, dtype=str, encoding='utf-8-sig', sep=sep, low_memory=False, **kwargs)

class LoanTapeLoader:
    _LOAN_NAMES = ('loan_data.csv', 'loan_tape.csv', 'prestamos.csv')
    _SCHED_NAMES = ('payment_schedule.csv', 'schedule.csv', 'cronograma.csv')
    _REAL_NAMES = ('real_payment.csv', 'payments.csv', 'pagos_reales.csv')
    _CUST_NAMES = ('customer_data.csv', 'customer.csv', 'customers.csv', 'clientes.csv')
    _COLL_NAMES = ('collateral.csv', 'garantias.csv')

    def __init__(self, source_tag: str='loan_tape', data_dir: str | Path='data/raw') -> None:
        self.source_tag = source_tag
        self.data_dir = Path(data_dir)

    def load_all(self, data_dir: str | Path | None=None, *, loan_path: Optional[str | Path]=None, schedule_path: Optional[str | Path]=None, real_payment_path: Optional[str | Path]=None, customer_path: Optional[str | Path]=None, collateral_path: Optional[str | Path]=None) -> dict[str, pd.DataFrame]:
        base = Path(data_dir) if data_dir else self.data_dir
        tables: dict[str, pd.DataFrame] = {}
        lp = Path(loan_path) if loan_path else self._find(base, self._LOAN_NAMES)
        sp = Path(schedule_path) if schedule_path else self._find(base, self._SCHED_NAMES)
        rp = Path(real_payment_path) if real_payment_path else self._find(base, self._REAL_NAMES)
        if lp:
            tables['dim_loan'] = self.load_loan_data(lp)
        else:
            logger.warning('loan_data file not found in %s — dim_loan will be empty', base)
            tables['dim_loan'] = pd.DataFrame(columns=DIM_LOAN_COLUMNS)
        if sp:
            tables['fact_schedule'] = self.load_schedule(sp)
        else:
            logger.warning('payment_schedule file not found — fact_schedule will be empty')
            tables['fact_schedule'] = pd.DataFrame(columns=FACT_SCHEDULE_COLUMNS)
        if rp:
            tables['fact_real_payment'] = self.load_real_payment(rp)
        else:
            logger.warning('real_payment file not found — fact_real_payment will be empty')
            tables['fact_real_payment'] = pd.DataFrame(columns=FACT_REAL_PAYMENT_COLUMNS)
        cp = Path(customer_path) if customer_path else self._find(base, self._CUST_NAMES)
        if cp:
            tables['dim_customer'] = self.load_customer(cp)
        colp = Path(collateral_path) if collateral_path else self._find(base, self._COLL_NAMES)
        if colp:
            tables['dim_collateral'] = self.load_collateral(colp)
        logger.info('LoanTapeLoader: loaded tables: %s', {k: len(v) for k, v in tables.items()})
        return tables

    def load_loan_data(self, path: str | Path) -> pd.DataFrame:
        df = _read_csv(Path(path))
        df = _rename_cols(df, _LOAN_ALIASES)
        df = self._coerce_loan(df)
        df['source'] = self.source_tag
        return self._select(df, DIM_LOAN_COLUMNS)

    def load_schedule(self, path: str | Path) -> pd.DataFrame:
        df = _read_csv(Path(path))
        df = _rename_cols(df, _SCHEDULE_ALIASES)
        df = self._coerce_schedule(df)
        return self._select(df, FACT_SCHEDULE_COLUMNS)

    def load_real_payment(self, path: str | Path) -> pd.DataFrame:
        df = _read_csv(Path(path))
        df = _rename_cols(df, _REAL_PAYMENT_ALIASES)
        df = self._coerce_payment(df)
        return self._select(df, FACT_REAL_PAYMENT_COLUMNS)

    def load_customer(self, path: str | Path) -> pd.DataFrame:
        df = _read_csv(Path(path))
        df = _rename_cols(df, _CUSTOMER_ALIASES)
        return self._select(df, DIM_CUSTOMER_COLUMNS)

    def load_collateral(self, path: str | Path) -> pd.DataFrame:
        df = _read_csv(Path(path))
        df = _rename_cols(df, _COLLATERAL_ALIASES)
        df = self._coerce_collateral(df)
        return self._select(df, DIM_COLLATERAL_COLUMNS)

    def _coerce_loan(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ['disbursement_date', 'maturity_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce', format='mixed')
        for col in ['original_principal', 'interest_rate']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if 'term_months' in df.columns:
            df['term_months'] = pd.to_numeric(df['term_months'], errors='coerce').astype('Int64')
        return df

    def _coerce_schedule(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'scheduled_date' in df.columns:
            df['scheduled_date'] = pd.to_datetime(df['scheduled_date'], errors='coerce', format='mixed')
        for col in ['scheduled_total', 'scheduled_principal', 'scheduled_interest', 'scheduled_fee', 'scheduled_other']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        if 'installment_number' in df.columns:
            df['installment_number'] = pd.to_numeric(df['installment_number'], errors='coerce').astype('Int64')
        return df

    def _coerce_payment(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'payment_date' in df.columns:
            df['payment_date'] = pd.to_datetime(df['payment_date'], errors='coerce', format='mixed')
        for col in ['paid_total', 'paid_principal', 'paid_interest', 'paid_fee', 'paid_other']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        return df

    def _coerce_collateral(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'collateral_value' in df.columns:
            df['collateral_value'] = pd.to_numeric(df['collateral_value'], errors='coerce')
        return df

    @staticmethod
    def _select(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        present = [c for c in columns if c in df.columns]
        extra = [c for c in df.columns if c not in columns]
        return df[present + extra].reset_index(drop=True)

    @staticmethod
    def _find(base: Path, names: tuple[str, ...]) -> Optional[Path]:
        for name in names:
            p = base / name
            if p.exists():
                return p
        return None
