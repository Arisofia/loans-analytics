"""
⚠️ DEPRECATED MODULE - DO NOT USE

This module is deprecated as of 2025-12-26.

Migration Instructions:
========================

Old code using kpi_engine.py:
    from python.kpi_engine import KPIEngine
    engine = KPIEngine(df)
    results = engine.calculate_metric("PAR30")

Should be updated to:
    from python.kpi_engine_v2 import KPIEngineV2
    engine = KPIEngineV2(df)
    results = engine.calculate_all()
    par30_value = results["PAR30"]["value"]

Key Differences:
- KPIEngineV2 has integrated audit trail logging
- Results include context and metadata
- Error handling is more robust
- All calculations are validated

Timeline:
- Use kpi_engine_v2.py immediately
- This file will be deleted in v2.0 (scheduled 2026-02-01)

Questions? Contact: engineering-team@abaco.com
"""

raise DeprecationWarning(
    "KPIEngine (v1) is deprecated. Use KPIEngineV2 instead. "
    "See migration instructions in this module."
)
