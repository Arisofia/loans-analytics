"""
Unified output integrations for Figma, Azure, Supabase, Meta, Notion, and other platforms.

This module provides a factory pattern for creating and managing output handlers
for scheduled batch exports (daily/hourly) and real-time KPI/analytics syncs.
"""

from src.integrations.azure_outputs import (AzureDashboardClient,
                                            AzureStorageClient)
from src.integrations.figma_client import FigmaClient
from src.integrations.meta_client import MetaOutputClient
from src.integrations.notion_client import NotionOutputClient
from src.integrations.supabase_client import SupabaseOutputClient

__all__ = [
    "FigmaClient",
    "AzureStorageClient",
    "AzureDashboardClient",
    "SupabaseOutputClient",
    "MetaOutputClient",
    "NotionOutputClient",
]
