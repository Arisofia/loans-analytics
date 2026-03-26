from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_metric_registry(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
