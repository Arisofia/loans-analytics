"""
Unified Pipeline Package - 4-Phase Architecture

This package implements the unified data pipeline with four sequential phases:
1. Ingestion - Data collection and validation
2. Transformation - Data cleaning and normalization
3. Calculation - KPI computation and enrichment
4. Output - Results distribution and storage
"""

__version__ = "2.0.0"
__all__ = [
    "orchestrator",
    "ingestion",
    "transformation",
    "calculation",
    "output",
    "config",
]
