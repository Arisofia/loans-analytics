from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Optional
import pandas as pd
logger = logging.getLogger(__name__)
_NUMERO_DESEMBOLSO_CANDIDATES = ['NumeroDesembolso', 'numero_desembolso', 'Numero_Desembolso', 'No_Desembolso', 'nro_desembolso', 'loan_ref', 'LoanRef']
_LEND_ID_CANDIDATES = ['lend_id', 'LendId', 'loan_id', 'LoanId', 'id_prestamo', 'id']

def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None

class LendIdMapper:

    def __init__(self, mapping_df: pd.DataFrame | None=None) -> None:
        if mapping_df is not None:
            self._df = mapping_df.copy()
            self._build_indices()
        else:
            self._df = pd.DataFrame(columns=['lend_id', 'numero_desembolso'])
            self._lend_to_num: dict[str, str] = {}
            self._num_to_lend: dict[str, str] = {}

    def load_from_csv(self, path: str | Path, *, lend_id_col: str | None=None, numero_desembolso_col: str | None=None) -> 'LendIdMapper':
        df = pd.read_csv(path, dtype=str, low_memory=False)
        logger.info('Loaded %d rows from %s', len(df), path)
        lid_col = lend_id_col or _find_col(df, _LEND_ID_CANDIDATES)
        num_col = numero_desembolso_col or _find_col(df, _NUMERO_DESEMBOLSO_CANDIDATES)
        if lid_col is None and num_col is None:
            raise ValueError(f'Cannot find lend_id or NumeroDesembolso columns in {path}. Available: {list(df.columns)}')
        if lid_col is None:
            logger.warning('lend_id column not found — generating from NumeroDesembolso')
            df['lend_id'] = df[num_col].apply(_normalize_id)
            lid_col = 'lend_id'
        if num_col is None:
            logger.warning('NumeroDesembolso column not found — using lend_id as-is')
            df['numero_desembolso'] = df[lid_col].apply(_normalize_id)
            num_col = 'numero_desembolso'
        new_pairs = df[[lid_col, num_col]].dropna().rename(columns={lid_col: 'lend_id', num_col: 'numero_desembolso'}).drop_duplicates()
        self._df = pd.concat([self._df, new_pairs], ignore_index=True).drop_duplicates(subset=['lend_id', 'numero_desembolso']).reset_index(drop=True)
        self._build_indices()
        logger.info('Mapping now contains %d pairs', len(self._df))
        return self

    def load_from_parquet(self, path: str | Path) -> 'LendIdMapper':
        self._df = pd.read_parquet(path)
        self._build_indices()
        return self

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._df.to_parquet(path, index=False)
        logger.info('Mapping saved → %s (%d pairs)', path, len(self._df))

    def to_lend_id(self, numero_desembolso: str) -> str | None:
        return self._num_to_lend.get(_normalize_id(numero_desembolso))

    def to_numero_desembolso(self, lend_id: str) -> str | None:
        return self._lend_to_num.get(_normalize_id(lend_id))

    def enrich_dataframe(self, df: pd.DataFrame, source_col: str, target_col: str, direction: str='auto') -> pd.DataFrame:
        df = df.copy()
        if direction == 'auto':
            direction = 'to_lend_id' if any((c in source_col.lower() for c in ('numero', 'desembolso', 'nde'))) else 'to_numero_desembolso'
        resolve_fn = self.to_lend_id if direction == 'to_lend_id' else self.to_numero_desembolso
        df[target_col] = df[source_col].apply(lambda v: resolve_fn(str(v)) if pd.notna(v) else None)
        return df

    def _build_indices(self) -> None:
        self._lend_to_num = dict(zip(self._df['lend_id'].apply(_normalize_id), self._df['numero_desembolso']))
        self._num_to_lend = dict(zip(self._df['numero_desembolso'].apply(_normalize_id), self._df['lend_id']))

    def __len__(self) -> int:
        return len(self._df)

    def __repr__(self) -> str:
        return f'LendIdMapper({len(self._df)} pairs)'

def _normalize_id(value: str) -> str:
    return re.sub('\\s+', '', str(value)).upper()
