"""Generate data manifest with metadata about datasets."""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict


def generate_manifest(data_dir: str = "data") -> Dict:
    """
    Generate data manifest with metadata.
    
    Args:
        data_dir: Directory containing data files
        
    Returns:
        Dictionary with manifest metadata
    """
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0",
        "datasets": []
    }
    
    data_path = Path(data_dir)
    if data_path.exists():
        for file_path in data_path.glob("*.json"):
            manifest["datasets"].append({
                "name": file_path.stem,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
    
    return manifest


def save_manifest(manifest: Dict, output_path: str = "data/manifest.json"):
    """
    Save manifest to JSON file.
    
    Args:
        manifest: Manifest dictionary
        output_path: Output file path
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved to {output_path}")


if __name__ == "__main__":
    manifest = generate_manifest()
    save_manifest(manifest)
