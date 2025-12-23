import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests

FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
FIGMA_FILE_KEY = os.getenv("FIGMA_FILE_KEY")
FIGMA_PAGE_NAME = "KPI Table"
BASE_URL = "https://api.figma.com/v1"

ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = [
    ROOT / "exports" / "KPI_Mapping_Table_for_Presentation.md",
    ROOT / "exports" / "KPI_Mapping_Table.csv",
]


class SyncError(RuntimeError):
    pass


def _gather_export_text(paths: Iterable[Path]) -> str:
    sections = []
    for path in paths:
        if not path.exists():
            raise SyncError(f"Missing export file: {path}")
        content = path.read_text(encoding="utf-8").strip()
        sections.append(f"### {path.name}\n{content}")
    return "\n\n".join(sections)


def _locate_page_node(file_data: dict, page_name: str) -> str:
    for child in file_data.get("document", {}).get("children", []):
        if child.get("name") == page_name:
            return child.get("id")
    raise SyncError(f"Page '{page_name}' not found in Figma file metadata.")


def _validate_configuration() -> dict:
    if not FIGMA_TOKEN:
        raise SyncError("FIGMA_TOKEN environment variable is required for Figma sync.")
    if not FIGMA_FILE_KEY:
        raise SyncError("FIGMA_FILE_KEY environment variable is required for Figma sync.")
    return {"X-Figma-Token": FIGMA_TOKEN}


def main() -> None:
    headers = _validate_configuration()
    combined_text = _gather_export_text(DATA_FILES)
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {
        "type": "TEXT",
        "characters": f"Synced KPI exports at {timestamp} (UTC)\n\n{combined_text}",
        "style": {"fontFamily": "Roboto", "fontSize": 12},
    }

    file_url = f"{BASE_URL}/files/{FIGMA_FILE_KEY}"
    try:
        response = requests.get(file_url, headers=headers, timeout=30)
        response.raise_for_status()
        file_data = response.json()
    except requests.exceptions.RequestException as exc:
        raise SyncError(f"Error fetching Figma file metadata: {exc}") from exc

    page_node_id = _locate_page_node(file_data, FIGMA_PAGE_NAME)
    update_url = f"{BASE_URL}/files/{FIGMA_FILE_KEY}/nodes?ids={page_node_id}"
    try:
        update_resp = requests.put(update_url, headers=headers, data=json.dumps(payload), timeout=30)
        update_resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise SyncError(f"Error updating Figma node: {exc}") from exc

    print(f"KPI table synced to Figma at {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    try:
        main()
    except SyncError as exc:
        raise SystemExit(exc)
