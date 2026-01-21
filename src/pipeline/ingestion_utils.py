from typing import List, Iterable, Optional
import re
import pandas as pd

def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

def select_column(columns: List[str], candidates: Iterable[str]) -> Optional[str]:
    if not candidates:
        return None
    lower_map = {col.lower(): col for col in columns}
    for candidate in candidates:
        key = str(candidate).lower()
        if key in lower_map:
            return lower_map[key]
    normalized_map = {normalize_token(col): col for col in columns}
    for candidate in candidates:
        key = normalize_token(candidate)
        if key in normalized_map:
            return normalized_map[key]
    return None

def match_metric(metric_name: str, mapping: dict) -> Optional[str]:
    metric_name_norm = normalize_token(metric_name)
    for key, candidates in mapping.items():
        if metric_name_norm == normalize_token(key):
            return key
        for candidate in candidates:
            if metric_name_norm == normalize_token(candidate):
                return key
    return None
