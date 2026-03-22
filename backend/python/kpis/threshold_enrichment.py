"""Enrich KPI exports with threshold status metadata for dashboard consumption."""

from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import yaml


def _extract_kpi_thresholds_from_section(
    section_value: dict, thresholds_map: dict[str, dict]
) -> None:
    """Populate thresholds_map from one registry section."""
    for kpi_name, kpi_def in section_value.items():
        if isinstance(kpi_def, dict) and "thresholds" in kpi_def:
            thresholds_map[kpi_name] = kpi_def["thresholds"]
        if isinstance(kpi_def, dict) and "id" in kpi_def:
            kpi_id = kpi_def["id"]
            if "thresholds" in kpi_def:
                thresholds_map[kpi_id] = kpi_def["thresholds"]


def _eval_high_is_good(value: float, critical_thresh: float, warning_thresh: float) -> str:
    """Status when higher values are better (e.g. collection rate)."""
    if value >= critical_thresh:
        return "normal"
    if value >= warning_thresh:
        return "warning"
    return "critical"


def _eval_low_is_good(value: float, critical_thresh: float, warning_thresh: float) -> str:
    """Status when lower values are better (e.g. days past due)."""
    if value <= critical_thresh:
        return "normal"
    if value <= warning_thresh:
        return "warning"
    return "critical"


def _eval_only_critical(value: float, critical_thresh: float) -> str:
    """Status when only critical threshold exists."""
    return "warning" if value >= critical_thresh else "critical"


def _eval_only_warning(value: float, warning_thresh: float) -> str:
    """Status when only warning threshold exists."""
    return "normal" if value >= warning_thresh else "warning"


def load_kpi_thresholds() -> dict[str, dict]:
    """Load KPI threshold configs from SSOT registry."""
    registry_path = Path(__file__).resolve().parents[3] / "config" / "kpis" / "kpi_definitions.yaml"
    if not registry_path.exists():
        return {}

    with registry_path.open("r", encoding="utf-8") as handle:
        registry = yaml.safe_load(handle) or {}

    # Flatten registry into simple kpi_name -> thresholds mapping
    thresholds_map: dict[str, dict] = {}
    for section_key, section_value in registry.items():
        if not section_key.endswith("_kpis") or not isinstance(section_value, dict):
            continue
        _extract_kpi_thresholds_from_section(section_value, thresholds_map)

    return thresholds_map


def get_threshold_status(
    kpi_value: float | int | Decimal,
    thresholds: Optional[dict[str, float | int | Decimal]] = None,
) -> str:
    """
    Determine normalized threshold status from a KPI value and threshold config.

    Args:
        kpi_value: The KPI metric value
        thresholds: Dict with optional keys: critical, warning, target
                   Supports both direction conventions:
                   - High-is-good: warning/critical are minimum targets
                   - Low-is-good: warning/critical are maximum targets

    Returns:
        One of: "normal", "warning", "critical", "not_configured"
    """
    if not thresholds or not isinstance(thresholds, dict):
        return "not_configured"

    # Convert to float for comparison
    value = float(kpi_value)

    # Extract thresholds, handling both naming conventions
    critical_val = thresholds.get("critical")
    warning_val = thresholds.get("warning")
    # No usable thresholds
    if critical_val is None and warning_val is None:
        return "not_configured"

    # Infer direction from available thresholds
    # If critical > warning or target, assume high-is-good (e.g., collection rate)
    # If critical < warning or target, assume low-is-good (e.g., days past due)

    # Simple heuristic: if we have both critical and warning, compare them
    if critical_val is not None and warning_val is not None:
        critical_thresh = float(critical_val)
        warning_thresh = float(warning_val)
        return (
            _eval_high_is_good(value, critical_thresh, warning_thresh)
            if critical_thresh > warning_thresh
            else _eval_low_is_good(value, critical_thresh, warning_thresh)
        )

    if critical_val is not None:
        return _eval_only_critical(value, float(critical_val))

    if warning_val is not None:
        return _eval_only_warning(value, float(warning_val))


def enrich_kpis_with_thresholds(
    kpi_snapshot: dict[str, Any],
    thresholds_map: Optional[dict[str, dict]] = None,
) -> dict[str, dict[str, Any]]:
    """
    Transform flat KPI values into rich objects with threshold metadata.

    Args:
        kpi_snapshot: Dict of {kpi_name: value}
        thresholds_map: Dict mapping kpi_name -> thresholds config.
                       If None, loads from SSOT registry.

    Returns:
        Dict of {kpi_name: {value: ..., threshold_status: ..., thresholds: ...}}
    """
    if thresholds_map is None:
        thresholds_map = load_kpi_thresholds()

    enriched = {}

    for kpi_name, value in kpi_snapshot.items():
        # Look up threshold config from registry
        thresholds = thresholds_map.get(kpi_name, {})
        threshold_status = get_threshold_status(value, thresholds)

        enriched[kpi_name] = {
            "value": value,
            "threshold_status": threshold_status,
            "thresholds": thresholds or {},
        }

    return enriched
