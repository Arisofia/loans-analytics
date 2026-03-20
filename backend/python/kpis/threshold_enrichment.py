"""Enrich KPI exports with threshold status metadata for dashboard consumption."""

from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml


def load_kpi_thresholds() -> dict[str, dict]:
    """Load KPI threshold configs from SSOT registry."""
    registry_path = (
        Path(__file__).resolve().parents[3] / "config" / "kpis" / "kpi_definitions.yaml"
    )
    if not registry_path.exists():
        return {}
    
    with registry_path.open("r", encoding="utf-8") as handle:
        registry = yaml.safe_load(handle) or {}
    
    # Flatten registry into simple kpi_name -> thresholds mapping
    thresholds_map: dict[str, dict] = {}
    for section_key, section_value in registry.items():
        if not section_key.endswith("_kpis") or not isinstance(section_value, dict):
            continue
        for kpi_name, kpi_def in section_value.items():
            if isinstance(kpi_def, dict) and "thresholds" in kpi_def:
                thresholds_map[kpi_name] = kpi_def["thresholds"]
            # Also map by ID if available
            if isinstance(kpi_def, dict) and "id" in kpi_def:
                kpi_id = kpi_def["id"]
                if "thresholds" in kpi_def:
                    thresholds_map[kpi_id] = kpi_def["thresholds"]
    
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
    target_val = thresholds.get("target")
    
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
        
        if critical_thresh > warning_thresh:
            # High-is-good: critical > warning, so higher values are better
            if value >= critical_thresh:
                return "normal"
            elif value >= warning_thresh:
                return "warning"
            else:
                return "critical"
        else:
            # Low-is-good: critical < warning, so lower values are better
            if value <= critical_thresh:
                return "normal"
            elif value <= warning_thresh:
                return "warning"
            else:
                return "critical"
    
    # Only critical available
    if critical_val is not None:
        critical_thresh = float(critical_val)
        if value >= critical_thresh:
            return "warning"
        else:
            return "critical"
    
    # Only warning available
    if warning_val is not None:
        warning_thresh = float(warning_val)
        if value >= warning_thresh:
            return "normal"
        else:
            return "warning"
    
    return "not_configured"


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
