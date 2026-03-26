from __future__ import annotations
import logging
import re
import unicodedata
from typing import Optional
import pandas as pd
logger = logging.getLogger(__name__)
try:
    rapidfuzz_module = __import__('rapidfuzz', fromlist=['fuzz', 'process'])
    fuzz = rapidfuzz_module.fuzz
    process = rapidfuzz_module.process
    RAPIDFUZZ_AVAILABLE = True
    logger.debug('RapidFuzz available — using optimised fuzzy matching')
except ImportError:
    import difflib
    RAPIDFUZZ_AVAILABLE = False
    logger.warning('rapidfuzz not installed — falling back to difflib (slower). pip install rapidfuzz')

def _normalize_name(name: str) -> str:
    nfd = unicodedata.normalize('NFD', str(name))
    ascii_str = nfd.encode('ascii', 'ignore').decode('ascii')
    upper = ascii_str.upper()
    cleaned = re.sub('[^A-Z0-9\\s]', ' ', upper)
    return re.sub('\\s+', ' ', cleaned).strip()

class FuzzyIncomeMatcher:

    def __init__(self, threshold: float=80.0, scorer: str='token_sort_ratio', max_workers: Optional[int]=None) -> None:
        self.threshold = threshold
        self.scorer = scorer
        self.max_workers = max_workers

    def match(self, left_df: pd.DataFrame, right_df: pd.DataFrame, left_on: str, right_on: str, score_col: str='fuzzy_score', matched_name_col: str='matched_name', keep_unmatched: bool=True) -> pd.DataFrame:
        left_names = left_df[left_on].fillna('').tolist()
        right_names = right_df[right_on].fillna('').tolist()
        norm_left = [_normalize_name(n) for n in left_names]
        norm_right = [_normalize_name(n) for n in right_names]
        match_records = self._vectorised_match(norm_left, norm_right, right_names)
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
        logger.info('FuzzyIncomeMatcher: %d/%d records matched (threshold=%.0f)', n_matched, len(left_df), self.threshold)
        return result

    def match_two_pass(self, left_df: pd.DataFrame, right_df: pd.DataFrame, left_on: str, right_on: str, exact_key: str | None=None, score_col: str='fuzzy_score', keep_unmatched: bool=True) -> pd.DataFrame:
        matched_positions: set[int] = set()
        exact_parts: list[pd.DataFrame] = []
        if exact_key and exact_key in left_df.columns and (exact_key in right_df.columns):
            left_tagged = left_df.copy()
            left_tagged['_pos'] = range(len(left_tagged))
            if right_df[exact_key].duplicated().any():
                logger.warning("Duplicate values detected for exact_key '%s' in right_df; dropping duplicates to enforce one-to-one exact matching.", exact_key)
                right_exact = right_df.drop_duplicates(subset=[exact_key])
            else:
                right_exact = right_df
            exact_merge = left_tagged.merge(right_exact, on=exact_key, how='inner', suffixes=('', '_right'))
            if not exact_merge.empty:
                exact_merge[score_col] = 100.0
                matched_positions.update(exact_merge['_pos'].tolist())
                exact_parts.append(exact_merge.drop(columns=['_pos']))
        unmatched_left = left_df.iloc[[i for i in range(len(left_df)) if i not in matched_positions]].copy()
        if len(unmatched_left) > 0:
            fuzzy_result = self.match(unmatched_left, right_df, left_on=left_on, right_on=right_on, score_col=score_col, keep_unmatched=keep_unmatched)
        else:
            fuzzy_result = pd.DataFrame()
        parts = [df for df in exact_parts + [fuzzy_result] if not df.empty]
        if not parts:
            return pd.DataFrame(columns=list(left_df.columns))
        combined = pd.concat(parts, ignore_index=True)
        logger.info('Two-pass: %d exact + %d fuzzy = %d total', sum((len(e) for e in exact_parts)), len(fuzzy_result), len(combined))
        return combined

    def _vectorised_match(self, queries: list[str], choices: list[str], original_choices: list[str]) -> list[tuple[str, Optional[int], float]]:
        if not choices:
            return [('', None, 0.0)] * len(queries)
        if RAPIDFUZZ_AVAILABLE:
            return self._rapidfuzz_match(queries, choices, original_choices)
        return self._difflib_match(queries, choices, original_choices)

    def _rapidfuzz_match(self, queries: list[str], choices: list[str], original_choices: list[str]) -> list[tuple[str, Optional[int], float]]:
        scorer_fn = getattr(fuzz, self.scorer, fuzz.token_sort_ratio)
        results: list[tuple[str, Optional[int], float]] = []
        for query in queries:
            match = process.extractOne(query, choices, scorer=scorer_fn)
            if match is None:
                results.append(('', None, 0.0))
            else:
                best_name_norm, best_score, best_idx = match
                results.append((original_choices[best_idx], best_idx, float(best_score)))
        return results

    def _difflib_match(self, queries: list[str], choices: list[str], original_choices: list[str]) -> list[tuple[str, Optional[int], float]]:
        results: list[tuple[str, Optional[int], float]] = []
        for query in queries:
            matches = difflib.get_close_matches(query, choices, n=1, cutoff=self.threshold / 100)
            if matches:
                best_norm = matches[0]
                best_idx = choices.index(best_norm)
                score = difflib.SequenceMatcher(None, query, best_norm).ratio() * 100
                results.append((original_choices[best_idx], best_idx, score))
            else:
                results.append(('', None, 0.0))
        return results
