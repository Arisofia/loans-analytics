"""
lend_id ↔ NumeroDesembolso mapper for overlapping months.

Control de Mora CSV files use ``NumeroDesembolso`` as the primary loan key,
while the unified pipeline uses ``lend_id``.  This module builds and persists
the bidirectional mapping so both identifiers can be used interchangeably.

Usage
-----
    mapper = LendIdMapper()
    mapper.load_from_csv("data/raw/control_mora_ene2026.csv")
    mapper.save("data/duckdb/lend_id_map.parquet")

    # Later, resolve:
    lend_id = mapper.to_lend_id("NDE-00123")
    numero   = mapper.to_numero_desembolso("L-20250045")
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Columns that may hold the NumeroDesembolso in Control-de-Mora exports
_NUMERO_DESEMBOLSO_CANDIDATES = [
    "NumeroDesembolso",
    "numero_desembolso",
    "Numero_Desembolso",
    "No_Desembolso",
    "nro_desembolso",
    "loan_ref",
    "LoanRef",
]

# Columns that may hold the lend_id in the unified pipeline output
_LEND_ID_CANDIDATES = [
    "lend_id",
    "LendId",
    "loan_id",
    "LoanId",
    "id_prestamo",
    "id",
]


def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first candidate column name present in *df*, or ``None``."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


class LendIdMapper:
    """Bidirectional mapping between ``lend_id`` and ``NumeroDesembolso``.

    The mapper is backed by a pandas DataFrame with columns
    ``lend_id`` and ``numero_desembolso`` (both ``str``).

    Parameters
    ----------
    mapping_df:
        Optional pre-built mapping DataFrame.
    """

    def __init__(self, mapping_df: pd.DataFrame | None = None) -> None:
        if mapping_df is not None:
            self._df = mapping_df.copy()
            self._build_indices()
        else:
            self._df = pd.DataFrame(columns=["lend_id", "numero_desembolso"])
            self._lend_to_num: dict[str, str] = {}
            self._num_to_lend: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Build / load
    # ------------------------------------------------------------------

    def load_from_csv(
        self,
        path: str | Path,
        *,
        lend_id_col: str | None = None,
        numero_desembolso_col: str | None = None,
    ) -> "LendIdMapper":
        """Extend the mapping by reading a Control-de-Mora CSV.

        Parameters
        ----------
        path:
            Path to the CSV file.
        lend_id_col:
            Override column name for ``lend_id``.  Auto-detected if ``None``.
        numero_desembolso_col:
            Override column name for ``NumeroDesembolso``.  Auto-detected if
            ``None``.

        Returns
        -------
        self
        """
        df = pd.read_csv(path, dtype=str, low_memory=False)
        logger.info("Loaded %d rows from %s", len(df), path)

        lid_col = lend_id_col or _find_col(df, _LEND_ID_CANDIDATES)
        num_col = numero_desembolso_col or _find_col(df, _NUMERO_DESEMBOLSO_CANDIDATES)

        if lid_col is None and num_col is None:
            raise ValueError(
                f"Cannot find lend_id or NumeroDesembolso columns in {path}. "
                f"Available: {list(df.columns)}"
            )

        # If only one is available, generate a synthetic key for the other
        if lid_col is None:
            logger.warning("lend_id column not found — generating from NumeroDesembolso")
            df["lend_id"] = df[num_col].apply(_normalize_id)
            lid_col = "lend_id"

        if num_col is None:
            logger.warning("NumeroDesembolso column not found — using lend_id as-is")
            df["numero_desembolso"] = df[lid_col].apply(_normalize_id)
            num_col = "numero_desembolso"

        new_pairs = (
            df[[lid_col, num_col]]
            .dropna()
            .rename(columns={lid_col: "lend_id", num_col: "numero_desembolso"})
            .drop_duplicates()
        )
        self._df = (
            pd.concat([self._df, new_pairs], ignore_index=True)
            .drop_duplicates(subset=["lend_id", "numero_desembolso"])
            .reset_index(drop=True)
        )
        self._build_indices()
        logger.info("Mapping now contains %d pairs", len(self._df))
        return self

    def load_from_parquet(self, path: str | Path) -> "LendIdMapper":
        """Load a previously saved mapping from a Parquet file."""
        self._df = pd.read_parquet(path)
        self._build_indices()
        return self

    def save(self, path: str | Path) -> None:
        """Persist the mapping to a Parquet file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._df.to_parquet(path, index=False)
        logger.info("Mapping saved → %s (%d pairs)", path, len(self._df))

    # ------------------------------------------------------------------
    # Resolve
    # ------------------------------------------------------------------

    def to_lend_id(self, numero_desembolso: str) -> str | None:
        """Resolve ``NumeroDesembolso`` → ``lend_id``.  Returns ``None`` if unknown."""
        return self._num_to_lend.get(_normalize_id(numero_desembolso))

    def to_numero_desembolso(self, lend_id: str) -> str | None:
        """Resolve ``lend_id`` → ``NumeroDesembolso``.  Returns ``None`` if unknown."""
        return self._lend_to_num.get(_normalize_id(lend_id))

    def enrich_dataframe(
        self,
        df: pd.DataFrame,
        source_col: str,
        target_col: str,
        direction: str = "auto",
    ) -> pd.DataFrame:
        """Add a resolved column to *df*.

        Parameters
        ----------
        df:
            Input DataFrame.
        source_col:
            Column containing the source identifier.
        target_col:
            Column name to create with the resolved identifier.
        direction:
            ``"to_lend_id"``, ``"to_numero_desembolso"``, or ``"auto"``
            (infers direction from *source_col* name).

        Returns
        -------
        pd.DataFrame
            Copy of *df* with *target_col* added.
        """
        df = df.copy()
        if direction == "auto":
            direction = (
                "to_lend_id"
                if any(c in source_col.lower() for c in ("numero", "desembolso", "nde"))
                else "to_numero_desembolso"
            )
        resolve_fn = self.to_lend_id if direction == "to_lend_id" else self.to_numero_desembolso
        df[target_col] = df[source_col].apply(lambda v: resolve_fn(str(v)) if pd.notna(v) else None)
        return df

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_indices(self) -> None:
        self._lend_to_num = dict(
            zip(
                self._df["lend_id"].apply(_normalize_id),
                self._df["numero_desembolso"],
            )
        )
        self._num_to_lend = dict(
            zip(
                self._df["numero_desembolso"].apply(_normalize_id),
                self._df["lend_id"],
            )
        )

    def __len__(self) -> int:
        return len(self._df)

    def __repr__(self) -> str:
        return f"LendIdMapper({len(self._df)} pairs)"


def _normalize_id(value: str) -> str:
    """Strip whitespace and normalize to uppercase for consistent lookups."""
    return re.sub(r"\s+", "", str(value)).upper()
