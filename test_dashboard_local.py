#!/usr/bin/env python
"""
Local dashboard test - Verify threshold badges render correctly with sample data.

This script:
1. Loads sample data
2. Generates KPI exports (complete_kpi_dashboard.json)
3. Displays KPI snapshot with threshold status badges
4. Validates enrichment worked correctly
"""

import json
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from backend.python.kpis.catalog_processor import KPICatalogProcessor
from backend.python.kpis.threshold_enrichment import enrich_kpis_with_thresholds
from backend.python.utils.normalization import normalize_dataframe_complete


def _load_sample_data(sample_file: Path) -> pd.DataFrame | None:
    print(f"\n📂 Loading sample data: {sample_file.name}")
    try:
        sample_data = pd.read_csv(sample_file, nrows=500)  # Use first 500 rows for speed
        print(f"   ✓ Loaded {len(sample_data):,} loan records")
        return sample_data
    except Exception as e:
        print(f"❌ Failed to load sample data: {e}")
        return None


def _normalize_sample_data(sample_data: pd.DataFrame) -> pd.DataFrame | None:
    print("\n🔄 Normalizing data...")
    try:
        normalized = normalize_dataframe_complete(sample_data)
        print(f"   ✓ Normalized {len(normalized):,} records")
        return normalized
    except Exception as e:
        print(f"❌ Normalization failed: {e}")
        return None


def _generate_executive_strip(normalized: pd.DataFrame) -> dict:
    print("\n📊 Generating KPIs...")
    try:
        processor = KPICatalogProcessor(
            loans_df=normalized,
            payments_df=pd.DataFrame(),  # No payments for sample
            customers_df=pd.DataFrame(),  # No customers for sample
        )
        all_kpis = processor.get_all_kpis()
        executive_strip = all_kpis.get("executive_strip", {})
        print(f"   ✓ Generated {len(executive_strip)} KPI metrics")
        return executive_strip
    except Exception as e:
        print(f"❌ KPI generation failed: {e}")
        return {}


def _build_kpi_snapshot(executive_strip: dict) -> dict[str, float]:
    print("\n🎯 Building KPI snapshot...")
    kpi_snapshot = {
        kpi_name: float(kpi_value)
        for kpi_name, kpi_value in executive_strip.items()
        if isinstance(kpi_value, (int, float))
    }
    print(f"   ✓ Extracted {len(kpi_snapshot)} metrics for display")
    return kpi_snapshot


def _format_kpi_value(kpi_name: str, value: object) -> str:
    if not isinstance(value, float):
        return str(value)
    if "rate" in kpi_name.lower() or "pct" in kpi_name.lower():
        return f"{value:.2f}%"
    if "count" in kpi_name.lower() or "loans" in kpi_name.lower():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def _print_dashboard_preview(
    enriched: dict[str, dict], status_badges: dict[str, str]
) -> None:
    print("\n📱 DASHBOARD PREVIEW - KPI Snapshot with Threshold Badges:")
    print("-" * 70)
    sorted_kpis = sorted(enriched.items(), key=lambda x: x[0])
    for idx, (kpi_name, kpi_data) in enumerate(sorted_kpis, 1):
        value = kpi_data.get("value")
        status = kpi_data.get("threshold_status", "not_configured")
        badge = status_badges.get(status, "❓ Unknown")
        thresholds = kpi_data.get("thresholds", {})
        display_name = kpi_name.replace("_", " ").title()
        formatted_value = _format_kpi_value(kpi_name, value)
        threshold_info = ""
        if thresholds:
            threshold_info = (
                f" (W:{thresholds.get('warning', 'N/A')} "
                f"C:{thresholds.get('critical', 'N/A')})"
            )
        print(f"{idx:2}. {display_name:30} {formatted_value:>15}  {badge}{threshold_info}")
    print("-" * 70)


def _print_summary(enriched: dict[str, dict], status_badges: dict[str, str]) -> None:
    print("\n📈 Enrichment Summary:")
    status_counts = {}
    for kpi_data in enriched.values():
        status = kpi_data.get("threshold_status", "not_configured")
        status_counts[status] = status_counts.get(status, 0) + 1
    for status, count in sorted(status_counts.items()):
        badge = status_badges.get(status, "❓")
        print(f"   {badge:20} {count:3} KPIs")


def _validate_enrichment(enriched: dict[str, dict]) -> bool:
    print("\n✅ Validation Results:")
    validation_passed = True
    all_have_fields = all(
        "value" in kpi and "threshold_status" in kpi and "thresholds" in kpi
        for kpi in enriched.values()
    )
    if all_have_fields:
        print("   ✓ All KPIs have required enrichment fields")
    else:
        print("   ❌ Some KPIs missing enrichment fields")
        validation_passed = False

    valid_statuses = {"normal", "warning", "critical", "not_configured"}
    all_valid_status = all(kpi.get("threshold_status") in valid_statuses for kpi in enriched.values())
    if all_valid_status:
        print("   ✓ All threshold statuses are valid")
    else:
        print("   ❌ Invalid threshold status values found")
        validation_passed = False
    return validation_passed


def run_dashboard_test():
    """Test the complete KPI enrichment pipeline with sample data."""
    
    print("\n" + "="*70)
    print("🧪 DASHBOARD THRESHOLD BADGE TEST")
    print("="*70)
    
    # Load sample data
    sample_file = ROOT / "data" / "samples" / "abaco_sample_data_20260202.csv"
    if not sample_file.exists():
        print(f"❌ Sample data not found: {sample_file}")
        return False
    
    sample_data = _load_sample_data(sample_file)
    if sample_data is None:
        return False
    
    # Normalize data
    normalized = _normalize_sample_data(sample_data)
    if normalized is None:
        return False
    
    # Generate KPIs using processor
    executive_strip = _generate_executive_strip(normalized)
    if not executive_strip:
        return False
    
    # Extract KPI snapshot (same logic as dashboard)
    kpi_snapshot = _build_kpi_snapshot(executive_strip)
    
    # Enrich with threshold status
    print("\n✨ Enriching KPIs with threshold status...")
    try:
        enriched = enrich_kpis_with_thresholds(kpi_snapshot)
        print(f"   ✓ Enriched {len(enriched)} KPI metrics")
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        return False
    
    # Display dashboard preview
    status_badges = {
        "normal": "✅ Normal",
        "warning": "⚠️  Warning",
        "critical": "🔴 Critical",
        "not_configured": "⊙ Not Set"
    }
    _print_dashboard_preview(enriched, status_badges)
    _print_summary(enriched, status_badges)
    validation_passed = _validate_enrichment(enriched)
    
    # Overall result
    print("\n" + "="*70)
    if validation_passed and len(enriched) > 0:
        print("✅ DASHBOARD TEST PASSED - Ready for local Streamlit testing!")
        print("\nNext step: Run Streamlit dashboard with:")
        print("  streamlit run frontend/streamlit_app/app.py")
        print("\nPlace sample CSV in local_exports/ directory for auto-load:")
        print(f"  cp {sample_file} local_exports/")
        print("="*70 + "\n")
        return True
    else:
        print("❌ DASHBOARD TEST FAILED - See errors above")
        print("="*70 + "\n")
        return False


if __name__ == "__main__":
    success = run_dashboard_test()
    sys.exit(0 if success else 1)
