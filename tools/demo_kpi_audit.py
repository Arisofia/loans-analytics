#!/usr/bin/env python
"""
Demo script for KPIEngineV2 audit trail functionality.

This script demonstrates the usage of KPIEngineV2 without requiring
full dependency installation. It shows:
- Creating a KPI engine instance
- Calculating KPIs
- Exporting audit trail to CSV

Run from repo root:
    python tools/demo_kpi_audit.py
"""

import sys
from pathlib import Path

# Add python directory to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

import pandas as pd


def demo_kpi_audit_trail():
    """Demonstrate KPIEngineV2 audit trail functionality."""
    print("=" * 60)
    print("KPIEngineV2 Audit Trail Demo")
    print("=" * 60)
    print()
    
    # Import KPIEngineV2 (will fail gracefully if dependencies missing)
    try:
        from python.kpis.engine import KPIEngineV2
    except ImportError as e:
        print(f"ERROR: Could not import KPIEngineV2: {e}")
        print("Please install required dependencies:")
        print("  pip install pandas polars pydantic pydantic-settings pyyaml")
        return 1
    
    # Create sample data
    print("1. Creating sample loan data...")
    sample_data = pd.DataFrame({
        "dpd_30_60_usd": [100.0, 200.0, 150.0],
        "dpd_60_90_usd": [50.0, 75.0, 100.0],
        "dpd_90_plus_usd": [25.0, 50.0, 75.0],
        "total_receivable_usd": [5000.0, 6000.0, 7000.0],
    })
    print(f"   Created DataFrame with {len(sample_data)} rows")
    print()
    
    # Initialize engine
    print("2. Initializing KPIEngineV2...")
    engine = KPIEngineV2(
        sample_data,
        actor="demo_script",
        run_id="demo_2026_01_29"
    )
    print(f"   Actor: {engine.actor}")
    print(f"   Run ID: {engine.run_id}")
    print()
    
    # Calculate individual KPI
    print("3. Calculating PAR30...")
    par30_value, par30_context = engine.calculate_par_30()
    print(f"   PAR30 Value: {par30_value}%")
    print(f"   Context: {par30_context}")
    print()
    
    # Calculate all KPIs
    print("4. Calculating all standard KPIs...")
    all_kpis = engine.calculate_all()
    print(f"   Calculated {len(all_kpis)} KPIs:")
    for kpi_name, kpi_data in all_kpis.items():
        print(f"     - {kpi_name}: {kpi_data['value']}")
    print()
    
    # Get audit trail
    print("5. Retrieving audit trail...")
    audit_df = engine.get_audit_trail()
    print(f"   Audit trail contains {len(audit_df)} records")
    print()
    print("   Audit Trail Preview:")
    print(audit_df.to_string(index=False))
    print()
    
    # Export audit trail
    print("6. Exporting audit trail to CSV...")
    exports_dir = repo_root / "exports"
    exports_dir.mkdir(exist_ok=True)
    
    output_path = exports_dir / "kpi_audit_trail.csv"
    audit_df.to_csv(output_path, index=False)
    print(f"   ✓ Exported to: {output_path}")
    print(f"   File size: {output_path.stat().st_size} bytes")
    print()
    
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(demo_kpi_audit_trail())
