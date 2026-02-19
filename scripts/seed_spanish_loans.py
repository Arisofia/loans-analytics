#!/usr/bin/env python3
"""Compatibility wrapper for archived Spanish loan identity generators."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_TARGET = (
    Path(__file__).resolve().parent.parent
    / "archives"
    / "maintenance"
    / "seed_spanish_loans.py"
)
_SPEC = importlib.util.spec_from_file_location("archived_seed_spanish_loans", _TARGET)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Cannot load archived module: {_TARGET}")

_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

for _name in dir(_MODULE):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_MODULE, _name)

