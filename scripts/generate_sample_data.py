#!/usr/bin/env python3
"""Compatibility wrapper for archived synthetic sample data generators."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_TARGET = (
    Path(__file__).resolve().parent.parent
    / "archives"
    / "maintenance"
    / "generate_sample_data.py"
)
_SPEC = importlib.util.spec_from_file_location("archived_generate_sample_data", _TARGET)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Cannot load archived module: {_TARGET}")

_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

for _name in dir(_MODULE):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_MODULE, _name)

