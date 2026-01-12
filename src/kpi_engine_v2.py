"""
Bridge for KPIEngineV2 to avoid duplication.
Points to the consolidated implementation in src.kpis.engine.
"""

from src.kpis.engine import KPIEngineV2

__all__ = ["KPIEngineV2"]
