"""
Fuzzy matcher for joining income records to disbursement records.

Uses RapidFuzz (or falls back to difflib) to match client names across
two DataFrames when exact joins fail due to typos, abbreviations, or
inconsistent formatting.

Usage
-----
    matcher = FuzzyIncomeMatcher(threshold=85)
    matched = matcher.match(
        income_df,
        disbursements_df,
        left_on="nombre_cliente",
        right_on="client_name",
        score_col="match_score",
    )
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

try:
    from rapidfuzz import fuzz, process  # type: ignore[import]

    RAPIDFUZZ_AVAILABLE = True
    logger.debug("RapidFuzz available — using optimised fuzzy matching")
except ImportError:
    import difflib  # noqa: PLC0415

    RAPIDFUZZ_AVAILABLE = False
    logger.warning(
        "rapidfuzz not installed — falling back to difflib (slower). "
        "pip install rapidfuzz"
    )


def _normalize_name(name: str) -> str:
    """Normalise a client name for fuzzy comparison.

    Steps
    -----
    1. Convert to ASCII (strip diacritics).
    2. Uppercase.
    3. Remove punctuation / extra whitespace.
    4. Collapse multiple spaces.
    """
    nfd = unicodedata.normalize("NFD", str(name))
    ascii_str = nfd.encode("ascii", "ignore").decode("ascii")
    upper = ascii_str.upper()
    cleaned = re.sub(r"[^A-Z0-9\s]", " ", upper)
    return re.sub(r"\s+", " ", cleaned).strip()


class FuzzyIncomeMatcher:
    """Match income records to disbursement records by client name.

    Parameters
    ----------
    threshold:
        Minimum similarity score (0–100) to consider a match.
        Defaults to ``80``.
    scorer:
        RapidFuzz scorer to use.  Defaults to ``token_sort_ratio``
        which handles word-order differences well.
    max_workers:
        Number of threads for parallel matching.  ``None`` uses all cores.
    """

    def __init__(
        self,
        threshold: float = 80.0,
        scorer: str = "token_sort_ratio",
        max_workers: Optional[int] = None,
    ) -> None:
        self.threshold = threshold
        self.scorer = scorer
        self.max_workers = max_workers

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        left_on: str,
        right_on: str,
        score_col: str = "fuzzy_score",
        matched_name_col: str = "matched_name",
        keep_unmatched: bool = True,
    ) -> pd.DataFrame:
        """Fuzzy-join *left_df* to *right_df* on name columns.

        Parameters
        ----------
        left_df:
            Income DataFrame (left side of join).
        right_df:
            Disbursement DataFrame (right side of join).
        left_on:
            Column name in *left_df* containing client names.
        right_on:
            Column name in *right_df* containing client names.
        score_col:
            Name of the column added to the result for the similarity score.
        matched_name_col:
            Name of the column added to the result for the matched name from
            *right_df*.
        keep_unmatched:
            When ``True`` (default), include left-side rows with no match
            (score < threshold).  Right-side join columns will be ``NaN``.

        Returns
        -------
        pd.DataFrame
            *left_df* enriched with columns from *right_df* plus *score_col*
            and *matched_name_col*.
        """
        left_names = left_df[left_on].fillna("").tolist()
        right_names = right_df[right_on].fillna("").tolist()

        norm_left = [_normalize_name(n) for n in left_names]
        norm_right = [_normalize_name(n) for n in right_names]

        match_records = self._vectorised_match(norm_left, norm_right, right_names)

        # Build result rows
        result_rows = []
        right_cols = [c for c in right_df.columns if c != right_on]

        for i, (best_name, best_idx, best_score) in enumerate(match_records):
            row = left_df.iloc[i].to_dict()
            row[score_col] = best_score
            row[matched_name_col] = best_name

            if best_score >= self.threshold and best_idx is not None:
                for col in right_cols:
                    row[col] = right_df.iloc[best_idx][col]
            elif not keep_unmatched:
                continue
            else:
                for col in right_cols:
                    row[col] = None

            result_rows.append(row)

        result = pd.DataFrame(result_rows)
        n_matched = (result[score_col] >= self.threshold).sum()
        logger.info(
            "FuzzyIncomeMatcher: %d/%d records matched (threshold=%.0f)",
            n_matched,
            len(left_df),
            self.threshold,
        )
        return result

    # ------------------------------------------------------------------
    # Exact-then-fuzzy two-pass strategy
    # ------------------------------------------------------------------

    def match_two_pass(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        exact_key: str,
        fuzzy_left: str,
        fuzzy_right: str,
        score_col: str = "fuzzy_score",
    ) -> pd.DataFrame:
        """Exact join first, then fuzzy for unmatched rows.

        Parameters
        ----------
        left_df:
            Income DataFrame.
        right_df:
            Disbursement DataFrame.
        exact_key:
            Column present in both DataFrames for the exact-join pass
            (e.g., ``client_id``).
        fuzzy_left / fuzzy_right:
            Name columns used for the fuzzy fallback.
        score_col:
            Score column added to fuzzy results.

        Returns
        -------
        pd.DataFrame
            Combined result from both passes.
        """
        # Pass 1: exact join
        # Preserve the original left_df index so we can correctly identify
        # which left rows participated in the exact match.
        left_with_idx = left_df.assign(_left_index=left_df.index)

        exact = left_with_idx.merge(
            right_df,
            on=exact_key,
            how="inner",
            suffixes=("", "_right"),
        )
        exact[score_col] = 100.0

        # matched_idx now correctly refers to the original left_df indices
        matched_idx = exact["_left_index"].unique()

        unmatched_left = left_df[~left_df.index.isin(matched_idx)].copy()

        if len(unmatched_left) == 0:
            # Drop helper column before returning to avoid changing the schema
            return exact.drop(columns=["_left_index"])

        # Pass 2: fuzzy match on the unmatched portion
        fuzzy_result = self.match(
            unmatched_left,
            right_df,
            left_on=fuzzy_left,
            right_on=fuzzy_right,
            score_col=score_col,
        )

        # Drop helper column used to track original left_df indices
        exact = exact.drop(columns=["_left_index"])

        combined = pd.concat([exact, fuzzy_result], ignore_index=True)
        logger.info(
            "Two-pass: %d exact + %d fuzzy = %d total",
            len(exact),
            len(fuzzy_result),
            len(combined),
        )
        return combined

    # ------------------------------------------------------------------
    # Internal matching logic
    # ------------------------------------------------------------------

    def _vectorised_match(
        self,
        queries: list[str],
        choices: list[str],
        original_choices: list[str],
    ) -> list[tuple[str, Optional[int], float]]:
        """Return (best_original_name, best_idx, best_score) for each query."""
        if not choices:
            return [("", None, 0.0)] * len(queries)

        if RAPIDFUZZ_AVAILABLE:
            return self._rapidfuzz_match(queries, choices, original_choices)
        return self._difflib_match(queries, choices, original_choices)

    def _rapidfuzz_match(
        self,
        queries: list[str],
        choices: list[str],
        original_choices: list[str],
    ) -> list[tuple[str, Optional[int], float]]:
        scorer_fn = getattr(fuzz, self.scorer, fuzz.token_sort_ratio)
        results = []
        for query in queries:
            match = process.extractOne(query, choices, scorer=scorer_fn)
            if match is None:
                results.append(("", None, 0.0))
            else:
                best_name_norm, best_score, best_idx = match
                results.append((original_choices[best_idx], best_idx, float(best_score)))
        return results

    def _difflib_match(
        self,
        queries: list[str],
        choices: list[str],
        original_choices: list[str],
    ) -> list[tuple[str, Optional[int], float]]:
        results = []
        for query in queries:
            matches = difflib.get_close_matches(query, choices, n=1, cutoff=self.threshold / 100)
            if matches:
                best_norm = matches[0]
                best_idx = choices.index(best_norm)
                score = difflib.SequenceMatcher(None, query, best_norm).ratio() * 100
                results.append((original_choices[best_idx], best_idx, score))
            else:
                results.append(("", None, 0.0))
        return results
