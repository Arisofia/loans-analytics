"""Generate data manifest with metadata about datasets."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config.paths import Paths


def generate_manifest(data_dir: Optional[str] = None) -> Dict:
    """
    Generate data manifest with metadata.

    Args:
        data_dir: Directory containing data files. Defaults to Paths.data_dir().

    Returns:
        Dictionary with manifest metadata
    """
    manifest = {"generated_at": datetime.now().isoformat(), "version": "1.0", "datasets": []}

    data_path = Path(data_dir) if data_dir else Paths.data_dir()
    if data_path.exists():
        for file_path in data_path.glob("*.json"):
            manifest["datasets"].append(
                {
                    "name": file_path.stem,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                }
            )

    return manifest


def save_manifest(manifest: Dict, output_path: Optional[str] = None):
    """
    Save manifest to JSON file.

    Args:
        manifest: Manifest dictionary
        output_path: Output file path. Defaults to data_dir / manifest.json
    """
    if output_path:
        out_file = Path(output_path)
    else:
        out_file = Paths.data_dir(create=True) / "manifest.json"

    os.makedirs(out_file.parent, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to {out_file}")


if __name__ == "__main__":
    manifest = generate_manifest()
    save_manifest(manifest)
