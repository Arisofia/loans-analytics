#!/usr/bin/env python3
"""Compatibility wrapper for service status report script.

This keeps legacy imports/tests working after the implementation moved to
archives/maintenance/generate_service_status_report.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


_TARGET = (
    Path(__file__).resolve().parent.parent
    / "archives"
    / "maintenance"
    / "generate_service_status_report.py"
)

_SPEC = importlib.util.spec_from_file_location("archived_service_status_report", _TARGET)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Cannot load archived module: {_TARGET}")

_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

ServiceStatusChecker = _MODULE.ServiceStatusChecker
generate_markdown_report = _MODULE.generate_markdown_report
main = _MODULE.main


if __name__ == "__main__":
    raise SystemExit(main())
