from __future__ import annotations
from decimal import Decimal
from typing import Any, Dict, Tuple
import pandas as pd
from backend.loans_analytics.validation import find_column, safe_decimal
_COLLECTED_CANDIDATES = ['payments_collected_usd', 'payments_collected', 'collections_usd', 'collection_amount_usd', 'collection_amount', 'amount_collected', 'total_collected_usd', 'total_collected', 'cash_collected_usd', 'cash_collected']
_DUE_CANDIDATES = ['payments_due_usd', 'payments_due', 'amount_due', 'total_due_usd', 'total_due', 'scheduled_payment_usd', 'scheduled_payment', 'expected_payment_usd', 'expected_payment', 'total_receivable_usd', 'total_receivable']

def _validate_series(df: pd.DataFrame, col: str) -> None:
    for val in df[col]:
        d_val = safe_decimal(val)
        if d_val < 0:
            raise ValueError(f'{col} contains negative values')

def calculate_collection_rate(df: pd.DataFrame | None) -> Tuple[Decimal, Dict[str, Any]]:
    if df is None or df.shape[0] == 0:
        return (Decimal('0.00'), {'rows_processed': 0, 'calculation_status': 'empty_input'})
    collected_col = find_column(df, _COLLECTED_CANDIDATES)
    due_col = find_column(df, _DUE_CANDIDATES)
    if collected_col is None or due_col is None:
        missing = [label for label, column in [('collected', collected_col), ('due', due_col)] if column is None]
        return (Decimal('0.00'), {'rows_processed': len(df), 'calculation_status': 'missing_columns', 'missing_columns': missing})
    _validate_series(df, collected_col)
    _validate_series(df, due_col)
    collected_total = sum((safe_decimal(val) for val in df[collected_col]))
    due_total = sum((safe_decimal(val) for val in df[due_col]))
    if due_total == 0:
        return (Decimal('0.00'), {'rows_processed': len(df), 'collected_column': collected_col, 'due_column': due_col, 'calculation_status': 'zero_due'})
    ratio = safe_decimal(collected_total / due_total)
    value = ratio * Decimal('100.0')
    return (value.quantize(Decimal('0.01')), {'rows_processed': len(df), 'collected_column': collected_col, 'due_column': due_col, 'collected_total': str(collected_total), 'due_total': str(due_total)})
