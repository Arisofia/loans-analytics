"""Lightweight loader for persisting ingestion outputs."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

LOG = logging.getLogger("ingest_loader")


class DataLoader:
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or "data")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _build_path(self, dataset: str, suffix: Optional[str], extension: str) -> Path:
        filename = f"{dataset}"
        if suffix:
            filename = f"{filename}_{suffix}"
        return self.base_path / f"{filename}.{extension}"

    def persist(self, df: pd.DataFrame, dataset: str, suffix: Optional[str] = None):
        csv_path = self._build_path(dataset, suffix, "csv")
        parquet_path = self._build_path(dataset, suffix, "parquet")
        df.to_csv(csv_path, index=False)
        df.to_parquet(parquet_path, index=False)
        LOG.info("Persisted dataset %s rows=%d csv=%s parquet=%s", dataset, len(df), csv_path, parquet_path)
        return csv_path, parquet_path

    def write_manifest(self, dataset: str, csv_path: Path, parquet_path: Path, extras: Optional[dict] = None) -> Path:
        manifest = {
            "dataset": dataset,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "csv": str(csv_path),
            "parquet": str(parquet_path),
        }
        if extras:
            manifest["extras"] = extras
        manifest_path = self.base_path / f"{dataset}_manifest.json"
        with manifest_path.open("w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        LOG.info("Wrote manifest %s", manifest_path)
        return manifest_path
