#!/usr/bin/env python3
"""Helpers for loading baseline data from JSON/YAML files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


def load_baselines(baseline_file: str) -> Dict[str, Any]:
    """Load baseline data from YAML or JSON file."""
    baseline_path = Path(baseline_file)
    if not baseline_path.exists():
        print(f"⚠️  Baseline file not found: {baseline_file}")
        return {}

    with open(baseline_path, encoding="utf-8") as handle:
        if baseline_file.endswith(".json"):
            return json.load(handle)
        if baseline_file.endswith((".yml", ".yaml")):
            if yaml is None:
                print("⚠️  PyYAML not installed, cannot read YAML baselines")
                return {}
            return yaml.safe_load(handle)

    return {}
