#!/usr/bin/env python3
"""
Cascade Debt Data Ingestion Script

This script downloads data from Cascade Debt platform and processes it using
the CascadeIngestion class for the Abaco portfolio.

Usage:
    python scripts/ingest_cascade.py [--loan-tape] [--financials] [--all]
    
Options:
    --loan-tape     Download and process loan tape export
    --financials    Download and process financial statements
    --all           Download all available data sources
    --output-dir    Output directory for processed data (default: data/cascade)
    
Environment Variables:
    CASCADE_USERNAME    Cascade Debt username
    CASCADE_PASSWORD    Cascade Debt password
    CASCADE_PID         Portfolio ID (default: abaco)

For manual downloads, use the URLs documented in CASCADE_DATA_SOURCES.md

For automated downloads, first run:
    python scripts/scrape_cascade.py --loan-tape
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
i
