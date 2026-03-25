from decimal import Decimal
from pathlib import Path
from typing import Any, Optional
import yaml

def _extract_kpi_thresholds_from_section(section_value: dict, thresholds_map: dict[str, dict]) -> None:
    for kpi_name, kpi_def in section_value.items():
        if not isinstance(kpi_def, dict):
            continue
        if 'thresholds' in kpi_def:
            thresholds_map[kpi_name] = kpi_def['thresholds']
        if 'id' in kpi_def and 'thresholds' in kpi_def:
            kpi_id = kpi_def['id']
            thresholds_map[kpi_id] = kpi_def['thresholds']

def _eval_high_is_good(value: float, critical_thresh: float, warning_thresh: float) -> str:
    if value >= critical_thresh:
        return 'normal'
    return 'warning' if value >= warning_thresh else 'critical'

def _eval_low_is_good(value: float, critical_thresh: float, warning_thresh: float) -> str:
    if value <= critical_thresh:
        return 'normal'
    return 'warning' if value <= warning_thresh else 'critical'

def _eval_only_critical(value: float, critical_thresh: float) -> str:
    return 'warning' if value >= critical_thresh else 'critical'

def _eval_only_warning(value: float, warning_thresh: float) -> str:
    return 'normal' if value >= warning_thresh else 'warning'

def load_kpi_thresholds() -> dict[str, dict]:
    registry_path = Path(__file__).resolve().parents[3] / 'config' / 'kpis' / 'kpi_definitions.yaml'
    if not registry_path.exists():
        return {}
    with registry_path.open('r', encoding='utf-8') as handle:
        registry = yaml.safe_load(handle) or {}
    thresholds_map: dict[str, dict] = {}
    for section_key, section_value in registry.items():
        if not section_key.endswith('_kpis') or not isinstance(section_value, dict):
            continue
        _extract_kpi_thresholds_from_section(section_value, thresholds_map)
    return thresholds_map

def get_threshold_status(kpi_value: float | int | Decimal, thresholds: Optional[dict[str, float | int | Decimal]]=None) -> str:
    if not thresholds or not isinstance(thresholds, dict):
        return 'not_configured'
    value = float(kpi_value)
    critical_val = thresholds.get('critical')
    warning_val = thresholds.get('warning')
    if critical_val is None and warning_val is None:
        return 'not_configured'
    if critical_val is not None and warning_val is not None:
        critical_thresh = float(critical_val)
        warning_thresh = float(warning_val)
        if critical_thresh > warning_thresh:
            return _eval_high_is_good(value, critical_thresh, warning_thresh)
        return _eval_low_is_good(value, critical_thresh, warning_thresh)
    if critical_val is not None:
        return _eval_only_critical(value, float(critical_val))
    return _eval_only_warning(value, float(warning_val))

def enrich_kpis_with_thresholds(kpi_snapshot: dict[str, Any], thresholds_map: Optional[dict[str, dict]]=None) -> dict[str, dict[str, Any]]:
    if thresholds_map is None:
        thresholds_map = load_kpi_thresholds()
    enriched = {}
    for kpi_name, value in kpi_snapshot.items():
        thresholds = thresholds_map.get(kpi_name, {})
        threshold_status = get_threshold_status(value, thresholds)
        enriched[kpi_name] = {'value': value, 'threshold_status': threshold_status, 'thresholds': thresholds or {}}
    return enriched
