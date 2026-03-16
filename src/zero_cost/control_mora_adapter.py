"""
Control de Mora CSV adapter.

Parses the legacy "Control de Mora" monthly spreadsheet exports and
normalises them to a canonical DataFrame compatible with the unified
Abaco pipeline.

Canonical output columns
------------------------
lend_id, numero_desembolso, client_id, client_name,
disbursement_date, currency, principal_outstanding,
total_overdue_amount, dpd, mora_bucket, snapshot_month,
product_type, branch_code
"""

from __future__ import annotations

import logging
import re
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column alias maps  (Control-de-Mora header → canonical name)
# ---------------------------------------------------------------------------
_ALIASES: dict[str, str] = {
    # Loan identifiers
    "numeroprestamo": "lend_id",
    "numero_prestamo": "lend_id",
    "loanid": "lend_id",
    "loan_id": "lend_id",
    "id_prestamo": "lend_id",
    "numerodesembolso": "numero_desembolso",
    "numero_desembolso": "numero_desembolso",
    "no_desembolso": "numero_desembolso",
    "nro_desembolso": "numero_desembolso",
    # Client
    "idcliente": "client_id",
    "id_cliente": "client_id",
    "clienteid": "client_id",
    "client_code": "client_id",
    "nombrecliente": "client_name",
    "nombre_cliente": "client_name",
    "clientename": "client_name",
    "borrower_name": "client_name",
    # Dates
    "fechadesembolso": "disbursement_date",
    "fecha_desembolso": "disbursement_date",
    "disbursementdate": "disbursement_date",
    "fechacorte": "snapshot_month",
    "fecha_corte": "snapshot_month",
    "mes_corte": "snapshot_month",
    # Amounts
    "saldovigente": "principal_outstanding",
    "saldo_vigente": "principal_outstanding",
    "saldocapital": "principal_outstanding",
    "saldo_capital": "principal_outstanding",
    "totalvencido": "total_overdue_amount",
    "total_vencido": "total_overdue_amount",
    "montovencido": "total_overdue_amount",
    "monto_vencido": "total_overdue_amount",
    # DPD / mora
    "dpd": "dpd",
    "diasmora": "dpd",
    "dias_mora": "dpd",
    "diasvencidos": "dpd",
    "dias_vencidos": "dpd",
    "bucketmora": "mora_bucket",
    "bucket_mora": "mora_bucket",
    "tramo": "mora_bucket",
    # Metadata
    "moneda": "currency",
    "currency": "currency",
    "producto": "product_type",
    "tipoproducto": "product_type",
    "product_type": "product_type",
    "sucursal": "branch_code",
    "codigosucursal": "branch_code",
    "branch_code": "branch_code",
}

_CANONICAL_COLUMNS = [
    "lend_id",
    "numero_desembolso",
    "client_id",
    "client_name",
    "disbursement_date",
    "currency",
    "principal_outstanding",
    "total_overdue_amount",
    "dpd",
    "mora_bucket",
    "snapshot_month",
    "product_type",
    "branch_code",
]

_DECIMAL_COLS = ["principal_outstanding", "total_overdue_amount"]
_INT_COLS = ["dpd"]


def _slugify(col: str) -> str:
    """Lowercase + strip special chars for column matching."""
    return re.sub(r"[^a-z0-9_]", "", col.strip().lower().replace(" ", "_"))


class ControlMoraAdapter:
    """Load and normalise Control-de-Mora CSV exports.

    Parameters
    ----------
    snapshot_month:
        ISO date string (``YYYY-MM-DD`` or ``YYYY-MM``) representing the
        reporting month.  When provided it overrides the value found in the
        CSV's own ``snapshot_month`` column.
    encoding:
        CSV file encoding.  Defaults to ``utf-8-sig`` to handle BOM-prefixed
        Excel exports.
    decimal:
        Decimal separator.  Defaults to ``.``.  Use ``,`` for Latin-American
        number formats.
    thousands:
        Thousands separator.  Defaults to ``,``.  Use ``.`` for Latin-American
        number formats.
    """

    def __init__(
        self,
        snapshot_month: Optional[str] = None,
        encoding: str = "utf-8-sig",
        decimal: str = ".",
        thousands: str = ",",
    ) -> None:
        self.snapshot_month = snapshot_month
        self.encoding = encoding
        self.decimal = decimal
        self.thousands = thousands

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, path: str | Path) -> pd.DataFrame:
        """Parse *path* and return a normalised DataFrame.

        Parameters
        ----------
        path:
            Path to the Control-de-Mora CSV or Excel file.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns matching ``_CANONICAL_COLUMNS`` (present
            columns only; missing canonical columns are silently omitted).
        """
        path = Path(path)
        df = self._read_file(path)
        df = self._rename_columns(df)
        df = self._coerce_types(df)
        df = self._apply_snapshot_month(df, path)
        df = self._ensure_canonical_columns(df)
        logger.info("ControlMoraAdapter: loaded %d rows from %s", len(df), path)
        return df

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_file(self, path: Path) -> pd.DataFrame:
        suffix = path.suffix.lower()
        if suffix in (".xlsx", ".xls"):
            return pd.read_excel(path, dtype=str)
        # CSV with optional BOM and semicolons
        raw = path.read_bytes()
        delimiter = ";" if b";" in raw[:2048] else ","
        return pd.read_csv(
            path,
            dtype=str,
            encoding=self.encoding,
            sep=delimiter,
            low_memory=False,
        )

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        mapping = {}
        for col in df.columns:
            canonical = _ALIASES.get(_slugify(col))
            if canonical:
                mapping[col] = canonical
        if mapping:
            logger.debug("Renaming columns: %s", mapping)
        return df.rename(columns=mapping)

    def _coerce_types(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in _DECIMAL_COLS:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(self.thousands, "", regex=False)
                    .str.replace(self.decimal, ".", regex=False)
                    .pipe(pd.to_numeric, errors="coerce")
                )
        for col in _INT_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        for col in ["disbursement_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=False)
        return df

    def _apply_snapshot_month(self, df: pd.DataFrame, path: Path) -> pd.DataFrame:
        if self.snapshot_month:
            # Normalize to month-end for consistent routing/aggregation semantics.
            raw = pd.to_datetime(self.snapshot_month)
            df["snapshot_month"] = (raw + pd.offsets.MonthEnd(0)).normalize()
        elif "snapshot_month" in df.columns:
            # Normalize existing column values to month-end.
            df["snapshot_month"] = pd.to_datetime(
                df["snapshot_month"], errors="coerce"
            ) + pd.offsets.MonthEnd(0)
        else:
            # Infer from filename pattern like "control_mora_ene2026.csv"
            match = re.search(r"(\d{4}[-_]\d{2}|\d{6}|\w{3}\d{4})", path.stem)
            if match:
                token = match.group(1)
                # Decide parsing strategy based on the matched pattern:
                #   - YYYY-MM or YYYY_MM
                #   - YYYYMM
                #   - 3-letter month token (possibly Spanish) + YYYY
                if re.fullmatch(r"\d{4}[-_]\d{2}", token):
                    # Normalize separator and parse as year-month
                    normalized = token.replace("_", "-")
                    df["snapshot_month"] = pd.to_datetime(
                        normalized, format="%Y-%m", errors="coerce"
                    )
                elif re.fullmatch(r"\d{6}", token):
                    # Compact year-month: YYYYMM
                    df["snapshot_month"] = pd.to_datetime(token, format="%Y%m", errors="coerce")
                else:
                    # Assume 3-letter month + 4-digit year, e.g. ene2026 / jan2026
                    month_token = token[:3].lower()
                    year_part = token[3:]
                    # Map common Spanish abbreviations to English so %b can parse them
                    es_to_en = {
                        "ene": "jan",
                        "feb": "feb",
                        "mar": "mar",
                        "abr": "apr",
                        "may": "may",
                        "jun": "jun",
                        "jul": "jul",
                        "ago": "aug",
                        "sep": "sep",
                        "oct": "oct",
                        "nov": "nov",
                        "dic": "dec",
                    }
                    normalized_month = es_to_en.get(month_token, month_token)
                    normalized = f"{normalized_month}{year_part}"
                    df["snapshot_month"] = pd.to_datetime(
                        normalized, format="%b%Y", errors="coerce"
                    )
                # Normalize inferred year-months to month-end to match pipeline semantics
                if "snapshot_month" in df.columns:
                    df["snapshot_month"] = (
                        df["snapshot_month"].dt.to_period("M").dt.to_timestamp("M")
                    )
            else:
                df["snapshot_month"] = pd.NaT
            if df["snapshot_month"].isna().all():
                message = (
                    f"Could not infer snapshot_month from filename '{path.name}'. "
                    "Set snapshot_month explicitly."
                )
                logger.warning(message)
                warnings.warn(message, UserWarning)
        return df

    def _ensure_canonical_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        present = [c for c in _CANONICAL_COLUMNS if c in df.columns]
        extra = [c for c in df.columns if c not in _CANONICAL_COLUMNS]
        return df[present + extra]

    # ------------------------------------------------------------------
    # Batch loading
    # ------------------------------------------------------------------

    @classmethod
    def load_many(
        cls,
        paths: list[str | Path],
        **kwargs,
    ) -> pd.DataFrame:
        """Load and concatenate multiple Control-de-Mora files.

        Parameters
        ----------
        paths:
            List of file paths.
        **kwargs:
            Passed to :class:`ControlMoraAdapter` constructor.

        Returns
        -------
        pd.DataFrame
            Combined and deduplicated DataFrame.
        """
        dfs = []
        for path in paths:
            adapter = cls(**kwargs)
            try:
                dfs.append(adapter.load(path))
            except (OSError, ValueError, pd.errors.ParserError) as exc:
                logger.error("Failed to load %s: %s", path, exc)
        if not dfs:
            return pd.DataFrame(columns=_CANONICAL_COLUMNS)
        combined = pd.concat(dfs, ignore_index=True)
        # Drop exact duplicates across (lend_id / numero_desembolso + snapshot_month)
        key_cols = [
            c for c in ["lend_id", "numero_desembolso", "snapshot_month"] if c in combined.columns
        ]
        if key_cols:
            combined = combined.drop_duplicates(subset=key_cols)
        return combined.reset_index(drop=True)
