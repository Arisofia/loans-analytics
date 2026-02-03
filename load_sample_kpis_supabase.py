"""Compatibility shim: re-exports scripts.load_sample_kpis_supabase for test imports."""

from scripts.load_sample_kpis_supabase import (
    KpiDataLoader,
    KpiRecord,
)

__all__ = ["KpiDataLoader", "KpiRecord"]
