#!/usr/bin/env python3
"""
Verify KPI coverage between codebase and Figma exports.
Checks if all KPIs defined in kpi_mapping.json are:
1. Computed in the analytics engine
2. Exported in fact tables
3. Properly documented for Figma display
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load_kpi_mapping() -> Dict:
    """Load KPI mapping configuration."""
    mapping_path = Path(__file__).parent.parent / "docs" / "analytics" / "kpi_mapping.json"
    if not mapping_path.exists():
        raise FileNotFoundError(f"KPI mapping file not found: {mapping_path}")
    
    with open(mapping_path, "r") as f:
        return json.load(f)


def load_python_file(file_path: Path) -> str:
    """Load and read a Python file."""
    if not file_path.exists():
        return ""
    
    with open(file_path, "r") as f:
        return f.read()


def check_kpi_in_analytics_engine() -> Tuple[List[str], List[str]]:
    """Check if KPIs are computed in enterprise_analytics_engine.py."""
    engine_path = Path(__file__).parent.parent / "apps" / "analytics" / "src" / "enterprise_analytics_engine.py"
    engine_code = load_python_file(engine_path)
    
    mapping = load_kpi_mapping()
    kpis = mapping["kpi_mapping"]
    
    found_kpis = []
    missing_kpis = []
    
    for kpi in kpis:
        kpi_id = kpi["kpi_id"]
        if kpi_id in engine_code or kpi["name"].lower() in engine_code.lower():
            found_kpis.append(kpi_id)
        else:
            missing_kpis.append(kpi_id)
    
    return found_kpis, missing_kpis


def check_kpi_in_streamlit_export() -> Tuple[List[str], List[str]]:
    """Check if KPIs are exported in streamlit_app.py."""
    streamlit_path = Path(__file__).parent.parent / "streamlit_app.py"
    streamlit_code = load_python_file(streamlit_path)
    
    mapping = load_kpi_mapping()
    exports = mapping["data_exports"]
    
    fact_table_exports = [e for e in exports if e["export_name"] == "abaco_fact_table.csv"]
    if not fact_table_exports:
        return [], []
    
    exported_metrics = fact_table_exports[0].get("contains_kpis", [])
    kpis = mapping["kpi_mapping"]
    
    found_kpis = []
    missing_kpis = []
    
    for kpi in kpis:
        metric_name = kpi["display_name"].lower().replace(" ", "_")
        if any(metric in streamlit_code for metric in [kpi["kpi_id"], metric_name, kpi["name"].lower()]):
            found_kpis.append(kpi["kpi_id"])
        else:
            missing_kpis.append(kpi["kpi_id"])
    
    return found_kpis, missing_kpis


def check_web_component_display() -> Tuple[List[str], List[str]]:
    """Check if KPIs are displayed in web components."""
    component_path = Path(__file__).parent.parent / "apps" / "web" / "src" / "components" / "analytics" / "PortfolioHealthKPIs.tsx"
    component_code = load_python_file(component_path)
    
    mapping = load_kpi_mapping()
    kpis = mapping["kpi_mapping"]
    
    found_kpis = []
    missing_kpis = []
    
    for kpi in kpis:
        if kpi["display_name"].lower() in component_code.lower() or kpi["kpi_id"] in component_code:
            found_kpis.append(kpi["kpi_id"])
        else:
            missing_kpis.append(kpi["kpi_id"])
    
    return found_kpis, missing_kpis


def verify_figma_section_coverage() -> Dict[str, List[str]]:
    """Verify KPIs are assigned to correct Figma sections."""
    mapping = load_kpi_mapping()
    sections = mapping["expected_figma_sections"]
    kpi_ids = {kpi["kpi_id"] for kpi in mapping["kpi_mapping"]}
    
    coverage = {}
    for section, kpis in sections.items():
        missing = [kpi for kpi in kpis if kpi not in kpi_ids]
        coverage[section] = {"total": len(kpis), "missing": missing}
    
    return coverage


def print_report():
    """Print comprehensive verification report."""
    print("\n" + "="*80)
    print("KPI COVERAGE VERIFICATION REPORT")
    print("="*80 + "\n")
    
    mapping = load_kpi_mapping()
    total_kpis = len(mapping["kpi_mapping"])
    
    analytics_found, analytics_missing = check_kpi_in_analytics_engine()
    print(f"1. ANALYTICS ENGINE")
    print(f"   Found: {len(analytics_found)}/{total_kpis} KPIs")
    if analytics_missing:
        print(f"   ⚠️  Missing: {', '.join(analytics_missing)}")
    else:
        print(f"   ✅ All KPIs computed")
    print()
    
    streamlit_found, streamlit_missing = check_kpi_in_streamlit_export()
    print(f"2. STREAMLIT EXPORT")
    print(f"   Found: {len(streamlit_found)}/{total_kpis} KPIs")
    if streamlit_missing:
        print(f"   ⚠️  Missing: {', '.join(streamlit_missing)}")
    else:
        print(f"   ✅ All KPIs exported")
    print()
    
    web_found, web_missing = check_web_component_display()
    print(f"3. WEB DISPLAY (PortfolioHealthKPIs.tsx)")
    print(f"   Found: {len(web_found)}/{total_kpis} KPIs")
    if web_missing:
        print(f"   ⚠️  Missing from display: {', '.join(web_missing)}")
    else:
        print(f"   ✅ All KPIs displayed")
    print()
    
    figma_coverage = verify_figma_section_coverage()
    print(f"4. FIGMA SECTION COVERAGE")
    for section, stats in figma_coverage.items():
        if stats["missing"]:
            print(f"   ⚠️  {section}: {stats['total']} KPIs expected, issues found")
            print(f"      Missing: {', '.join(stats['missing'])}")
        else:
            print(f"   ✅ {section}: {stats['total']} KPIs mapped")
    print()
    
    all_found = set(analytics_found) & set(streamlit_found) & set(web_found)
    coverage_percent = (len(all_found) / total_kpis) * 100 if total_kpis > 0 else 0
    
    print(f"5. OVERALL COVERAGE")
    print(f"   {len(all_found)}/{total_kpis} KPIs ({coverage_percent:.1f}%) fully covered")
    print(f"   Figma Export URL: {mapping['figma_export_url']}")
    print()
    
    if coverage_percent == 100:
        print("✅ ALL KPIs ARE PROPERLY COVERED AND READY FOR FIGMA")
    else:
        print(f"⚠️  {100 - coverage_percent:.1f}% of KPIs need verification/updates")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        print_report()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
