from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .kpi_models import KPISet


def save_kpi_set_json(kpi_set: KPISet, output_dir: str | Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = kpi_set.as_of.strftime("%Y%m%dT%H%M%S")
    filename = f"{kpi_set.id}_{timestamp}.json"
    path = output_dir / filename

    with path.open("w", encoding="utf-8") as handle:
        json.dump(kpi_set.to_dict(), handle, ensure_ascii=False, indent=2)

    latest_symlink = output_dir / f"{kpi_set.id}_latest.json"
    if latest_symlink.exists() or latest_symlink.is_symlink():
        latest_symlink.unlink()
    latest_symlink.symlink_to(path.name)

    return path


def load_latest_kpi_set_json(kpi_set_id: str, output_dir: str | Path) -> Dict:
    output_dir = Path(output_dir)
    latest_path = output_dir / f"{kpi_set_id}_latest.json"
    if not latest_path.exists():
        raise FileNotFoundError(f"No latest KPI file for id={kpi_set_id} in {output_dir}")
    with latest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_kpi_files(output_dir: str | Path) -> List[Path]:
    output_dir = Path(output_dir)
    return sorted(output_dir.glob("*.json"))
