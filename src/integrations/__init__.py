"""
Unified output integrations for Azure, Supabase, Meta, and other platforms.

This module provides a factory pattern for creating and managing output handlers
for scheduled batch exports (daily/hourly) and real-time KPI/analytics syncs.
"""

from src.integrations.azure_outputs import AzureDashboardClient, AzureStorageClient  # noqa: E402
from src.integrations.meta_client import MetaOutputClient  # noqa: E402
from src.integrations.supabase_client import SupabaseOutputClient  # noqa: E402

__all__ = [
    "AzureStorageClient",
    "AzureDashboardClient",
    "SupabaseOutputClient",
    "MetaOutputClient",
]
