"""Output writers for analytics-ready datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


def export_frames(frames: Dict[str, pd.DataFrame], output_dir: Path) -> Dict[str, Path]:
    """Export frames to Parquet and return paths."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {}
    for name, frame in frames.items():
        path = output_dir / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        paths[name] = path
    return paths
