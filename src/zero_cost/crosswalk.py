"""
Loan ID Crosswalk — maps ``loan_id`` (loan tape) ↔ ``operation_id`` (Control de Mora).

When a direct key exists in both systems, it is used as-is.
When no match is found, a fuzzy join on client name + disbursement date is
attempted and the result is recorded with a ``match_type`` and ``reason_code``.

Unmatched records are always exported to ``exports/unmatched_records.csv``.

Usage
-----
    cw = Crosswalk()
    cw.build(loan_tape_df, control_mora_df)
    cw.save("data/duckdb/crosswalk.parquet")
    cw.export_unmatched("exports/unmatched_records.csv")
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Reason codes
REASON_EXACT = "exact_key_match"
REASON_FUZZY = "fuzzy_name_date_match"
REASON_UNMATCHED_TAPE = "unmatched_loan_tape"
REASON_UNMATCHED_MORA = "unmatched_control_mora"
REASON_NOT_SPECIFIED = "not_specified"

try:
    from rapidfuzz import fuzz  # type: ignore[import]

    _RAPIDFUZZ = True
except ImportError:
    _RAPIDFUZZ = False


def _normalize(s: str) -> str:
    """Normalize a string for fuzzy comparison."""
    import unicodedata

    nfd = unicodedata.normalize("NFD", str(s))
    ascii_ = nfd.encode("ascii", "ignore").decode("ascii").upper()
    return re.sub(r"[^A-Z0-9]", "", ascii_)


def _name_score(a: str, b: str) -> float:
    """Return 0-100 similarity score for two names."""
    na, nb = _normalize(a), _normalize(b)
    if not na or not nb:
        return 0.0
    if _RAPIDFUZZ:
        return float(fuzz.token_sort_ratio(na, nb))
    ratio = __import__("difflib").SequenceMatcher(None, na, nb).ratio()
    return ratio * 100.0


class Crosswalk:
    """Build and manage the loan_id ↔ operation_id crosswalk.

    Parameters
    ----------
    fuzzy_name_threshold:
        Minimum name similarity score (0-100) for a fuzzy match.
    date_tolerance_days:
        Maximum allowed difference in disbursement dates for a fuzzy match.
    """

    def __init__(
        self,
        fuzzy_name_threshold: float = 80.0,
        date_tolerance_days: int = 7,
    ) -> None:
        self.fuzzy_name_threshold = fuzzy_name_threshold
        self.date_tolerance_days = date_tolerance_days
        self._df: pd.DataFrame = pd.DataFrame(
            columns=["loan_id", "operation_id", "match_type", "reason_code", "match_score"]
        )

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(
        self,
        loan_tape_df: pd.DataFrame,
        control_mora_df: pd.DataFrame,
        *,
        tape_id_col: str = "loan_id",
        mora_id_col: str = "lend_id",
        mora_numero_col: str = "numero_desembolso",
        tape_name_col: Optional[str] = None,
        mora_name_col: Optional[str] = "client_name",
        tape_date_col: Optional[str] = "disbursement_date",
        mora_date_col: Optional[str] = "disbursement_date",
    ) -> "Crosswalk":
        """Build the crosswalk from both DataFrames.

        Parameters
        ----------
        loan_tape_df:
            dim_loan from loan tape (contains ``loan_id``).
        control_mora_df:
            Normalized Control-de-Mora DataFrame (contains ``lend_id`` and/or
            ``numero_desembolso``).

        Returns
        -------
        self
        """
        records = []

        tape_ids = set(loan_tape_df[tape_id_col].dropna().astype(str))
        mora_ids: set[str] = set()
        if mora_id_col in control_mora_df.columns:
            mora_ids |= set(control_mora_df[mora_id_col].dropna().astype(str))
        if mora_numero_col in control_mora_df.columns:
            mora_ids |= set(control_mora_df[mora_numero_col].dropna().astype(str))

        # Pass 1: exact key match
        matched_tape: set[str] = set()
        matched_mora: set[str] = set()

        for tid in tape_ids:
            # Check against lend_id
            if mora_id_col in control_mora_df.columns:
                hit = control_mora_df[control_mora_df[mora_id_col].astype(str) == tid]
                if not hit.empty:
                    oid = str(hit[mora_id_col].iloc[0])
                    records.append(
                        {
                            "loan_id": tid,
                            "operation_id": oid,
                            "match_type": "exact",
                            "reason_code": REASON_EXACT,
                            "match_score": 100.0,
                        }
                    )
                    matched_tape.add(tid)
                    matched_mora.add(oid)
                    continue
            # Check against numero_desembolso
            if mora_numero_col in control_mora_df.columns:
                hit = control_mora_df[control_mora_df[mora_numero_col].astype(str) == tid]
                if not hit.empty:
                    oid = str(hit[mora_numero_col].iloc[0])
                    records.append(
                        {
                            "loan_id": tid,
                            "operation_id": oid,
                            "match_type": "exact",
                            "reason_code": REASON_EXACT,
                            "match_score": 100.0,
                        }
                    )
                    matched_tape.add(tid)
                    matched_mora.add(oid)

        # Pass 2: fuzzy match (name + date) for unmatched tape loans
        unmatched_tape = [tid for tid in tape_ids if tid not in matched_tape]
        if unmatched_tape and tape_name_col and mora_name_col:
            records += self._fuzzy_match(
                loan_tape_df,
                control_mora_df,
                unmatched_tape,
                matched_mora,
                tape_id_col=tape_id_col,
                mora_id_col=mora_id_col,
                mora_numero_col=mora_numero_col,
                tape_name_col=tape_name_col,
                mora_name_col=mora_name_col,
                tape_date_col=tape_date_col,
                mora_date_col=mora_date_col,
            )

        # Remaining unmatched — mark as no-match with reason_code
        final_matched_tape = {r["loan_id"] for r in records}
        for tid in tape_ids:
            if tid not in final_matched_tape:
                records.append(
                    {
                        "loan_id": tid,
                        "operation_id": None,
                        "match_type": "unmatched",
                        "reason_code": REASON_UNMATCHED_TAPE,
                        "match_score": 0.0,
                    }
                )

        final_matched_mora = {r["operation_id"] for r in records if r["operation_id"]}
        for mid in mora_ids:
            if mid not in final_matched_mora:
                records.append(
                    {
                        "loan_id": None,
                        "operation_id": mid,
                        "match_type": "unmatched",
                        "reason_code": REASON_UNMATCHED_MORA,
                        "match_score": 0.0,
                    }
                )

        self._df = pd.DataFrame(records)
        n_exact = (self._df["match_type"] == "exact").sum()
        n_fuzzy = (self._df["match_type"] == "fuzzy").sum()
        n_unmatched = (self._df["match_type"] == "unmatched").sum()
        logger.info(
            "Crosswalk: %d exact, %d fuzzy, %d unmatched",
            n_exact, n_fuzzy, n_unmatched,
        )
        return self

    # ------------------------------------------------------------------
    # Persist / load
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        """Save crosswalk to Parquet."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._df.to_parquet(path, index=False)
        logger.info("Crosswalk saved → %s (%d rows)", path, len(self._df))

    def load(self, path: str | Path) -> "Crosswalk":
        """Load a previously saved crosswalk from Parquet."""
        self._df = pd.read_parquet(path)
        return self

    def export_unmatched(self, path: str | Path) -> None:
        """Export unmatched records to CSV with reason_code populated.

        Always writes the file, even when there are no unmatched records
        (in that case the CSV has a header row only).
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        unmatched = self._df[self._df["match_type"] == "unmatched"].copy()
        # Ensure reason_code is never empty
        unmatched["reason_code"] = unmatched["reason_code"].fillna(REASON_NOT_SPECIFIED)
        unmatched.to_csv(path, index=False)
        logger.info("Unmatched records → %s (%d rows)", path, len(unmatched))

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def to_operation_id(self, loan_id: str) -> Optional[str]:
        """Resolve loan_id → operation_id."""
        hit = self._df[self._df["loan_id"] == loan_id]
        if hit.empty or hit["operation_id"].isna().all():
            return None
        return str(hit["operation_id"].iloc[0])

    def to_loan_id(self, operation_id: str) -> Optional[str]:
        """Resolve operation_id → loan_id."""
        hit = self._df[self._df["operation_id"] == operation_id]
        if hit.empty or hit["loan_id"].isna().all():
            return None
        return str(hit["loan_id"].iloc[0])

    def __len__(self) -> int:
        return len(self._df)

    def __repr__(self) -> str:
        return f"Crosswalk({len(self._df)} records)"

    # ------------------------------------------------------------------
    # Fuzzy matching internals
    # ------------------------------------------------------------------

    def _fuzzy_match(
        self,
        tape_df: pd.DataFrame,
        mora_df: pd.DataFrame,
        unmatched_ids: list[str],
        already_matched_mora: set[str],
        *,
        tape_id_col: str,
        mora_id_col: str,
        mora_numero_col: str,
        tape_name_col: str,
        mora_name_col: str,
        tape_date_col: Optional[str],
        mora_date_col: Optional[str],
    ) -> list[dict]:
        records = []
        mora_candidates = mora_df[~mora_df[mora_id_col].astype(str).isin(already_matched_mora)].copy()
        if mora_candidates.empty:
            return records

        mora_names = mora_candidates[mora_name_col].fillna("").tolist()
        mora_oper_ids = mora_candidates[mora_id_col].astype(str).tolist()

        tape_subset = tape_df[tape_df[tape_id_col].astype(str).isin(unmatched_ids)]

        for _, row in tape_subset.iterrows():
            tid = str(row[tape_id_col])
            t_name = str(row.get(tape_name_col, ""))
            t_date = pd.Timestamp(row[tape_date_col]) if tape_date_col and tape_date_col in row else None

            best_score, best_idx = 0.0, -1
            for i, m_name in enumerate(mora_names):
                score = _name_score(t_name, m_name)
                if score > best_score:
                    # Check date proximity
                    if t_date is not None and mora_date_col and mora_date_col in mora_candidates.columns:
                        m_date = pd.Timestamp(mora_candidates.iloc[i][mora_date_col])
                        if abs((t_date - m_date).days) > self.date_tolerance_days:
                            continue
                    best_score = score
                    best_idx = i

            if best_score >= self.fuzzy_name_threshold and best_idx >= 0:
                records.append(
                    {
                        "loan_id": tid,
                        "operation_id": mora_oper_ids[best_idx],
                        "match_type": "fuzzy",
                        "reason_code": REASON_FUZZY,
                        "match_score": best_score,
                    }
                )
            # Unmatched loans are added by the caller

        return records
