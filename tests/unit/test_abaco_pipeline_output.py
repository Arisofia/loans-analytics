from __future__ import annotations

import json
from datetime import datetime, timezone

from src.abaco_pipeline.output.manifests import RunManifest, write_manifest


def test_write_manifest_writes_json(tmp_path):
    created_at = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    manifest = RunManifest(
        run_id="run-123",
        created_at=created_at,
        inputs={"loans": "data/loans.csv"},
        outputs={"report": "exports/report.json"},
    )

    out = write_manifest(tmp_path / "manifest.json", manifest)
    assert out.exists()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-123"
    assert payload["created_at"] == created_at.isoformat()
    assert payload["inputs"]["loans"] == "data/loans.csv"
    assert payload["outputs"]["report"] == "exports/report.json"
