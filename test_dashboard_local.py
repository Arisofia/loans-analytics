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
    
    print(f"\n📂 Loading sample data: {sample_file.name}")
    try:
        sample_data = pd.read_csv(sample_file, nrows=500)  # Use first 500 rows for speed
        print(f"   ✓ Loaded {len(sample_data):,} loan records")
    except Exception as e:
        print(f"❌ Failed to load sample data: {e}")
        return False
    
    # Normalize data
    print(f"\n🔄 Normalizing data...")
    try:
        normalized = normalize_dataframe_complete(sample_data)
        print(f"   ✓ Normalized {len(normalized):,} records")
    except Exception as e:
        print(f"❌ Normalization failed: {e}")
        return False
    
    # Generate KPIs using processor
    print(f"\n📊 Generating KPIs...")
    try:
        processor = KPICatalogProcessor(
            loans_df=normalized,
            payments_df=pd.DataFrame(),  # No payments for sample
            customers_df=pd.DataFrame(),  # No customers for sample
        )
        all_kpis = processor.get_all_kpis()
        executive_strip = all_kpis.get("executive_strip", {})
        print(f"   ✓ Generated {len(executive_strip)} KPI metrics")
    except Exception as e:
        print(f"❌ KPI generation failed: {e}")
        return False
    
    # Extract KPI snapshot (same logic as dashboard)
    print(f"\n🎯 Building KPI snapshot...")
    kpi_snapshot = {}
    for kpi_name, kpi_value in executive_strip.items():
        if isinstance(kpi_value, (int, float)):
            kpi_snapshot[kpi_name] = float(kpi_value)
    
    print(f"   ✓ Extracted {len(kpi_snapshot)} metrics for display")
    
    # Enrich with threshold status
    print(f"\n✨ Enriching KPIs with threshold status...")
    try:
        enriched = enrich_kpis_with_thresholds(kpi_snapshot)
        print(f"   ✓ Enriched {len(enriched)} KPI metrics")
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        return False
    
    # Display dashboard preview
    print(f"\n📱 DASHBOARD PREVIEW - KPI Snapshot with Threshold Badges:")
    print("-" * 70)
    
    status_badges = {
        "normal": "✅ Normal",
        "warning": "⚠️  Warning",
        "critical": "🔴 Critical",
        "not_configured": "⊙ Not Set"
    }
    
    sorted_kpis = sorted(enriched.items(), key=lambda x: x[0])
    for idx, (kpi_name, kpi_data) in enumerate(sorted_kpis, 1):
        value = kpi_data.get("value")
        status = kpi_data.get("threshold_status", "not_configured")
        badge = status_badges.get(status, "❓ Unknown")
        thresholds = kpi_data.get("thresholds", {})
        
        # Format the name for display
        display_name = kpi_name.replace("_", " ").title()
        
        # Format value appropriately
        if isinstance(value, float):
            if "rate" in kpi_name.lower() or "pct" in kpi_name.lower():
                formatted_value = f"{value:.2f}%"
            elif "count" in kpi_name.lower() or "loans" in kpi_name.lower():
                formatted_value = f"{int(value):,}"
            else:
                formatted_value = f"{value:,.2f}"
        else:
            formatted_value = str(value)
        
        # Display with threshold info
        threshold_info = ""
        if thresholds:
            threshold_info = f" (W:{thresholds.get('warning', 'N/A')} C:{thresholds.get('critical', 'N/A')})"
        
        print(f"{idx:2}. {display_name:30} {formatted_value:>15}  {badge}{threshold_info}")
    
    print("-" * 70)
    
    # Summary statistics
    print(f"\n📈 Enrichment Summary:")
    status_counts = {}
    for kpi_data in enriched.values():
        status = kpi_data.get("threshold_status", "not_configured")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in sorted(status_counts.items()):
        badge = status_badges.get(status, "❓")
        print(f"   {badge:20} {count:3} KPIs")
    
    # Validate enrichment
    print(f"\n✅ Validation Results:")
    validation_passed = True
    
    # Check all KPIs have required fields
    all_have_fields = all(
        "value" in kpi and "threshold_status" in kpi and "thresholds" in kpi
        for kpi in enriched.values()
    )
    if all_have_fields:
        print(f"   ✓ All KPIs have required enrichment fields")
    else:
        print(f"   ❌ Some KPIs missing enrichment fields")
        validation_passed = False
    
    # Check all statuses are valid
    valid_statuses = {"normal", "warning", "critical", "not_configured"}
    all_valid_status = all(
        kpi.get("threshold_status") in valid_statuses
        for kpi in enriched.values()
    )
    if all_valid_status:
        print(f"   ✓ All threshold statuses are valid")
    else:
        print(f"   ❌ Invalid threshold status values found")
        validation_passed = False
    
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
