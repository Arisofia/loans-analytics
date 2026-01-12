import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config.paths import Paths  # noqa: E402
from src.config.secrets import get_secrets_manager  # noqa: E402

def main():
    # Secrets
    secrets = get_secrets_manager()
    try:
        # Prioritize environment variables for tests, fallback to secrets manager
        figma_token = os.getenv("FIGMA_TOKEN") or secrets.get("FIGMA_TOKEN", required=True)
        figma_file_key = os.getenv("FIGMA_FILE_KEY") or secrets.get("FIGMA_FILE_KEY", required=True)
    except Exception as e:
        print(f"Error getting secrets: {e}")
        return

    # Paths
    figma_page_name = "KPI Table"
    
    # Check EXPORTS_PATH env var for tests
    exports_dir = Path(os.getenv("EXPORTS_PATH", str(Paths.exports_dir())))
    csv_export_path = exports_dir / "KPI_Mapping_Table.csv"

    if not csv_export_path.exists():
        print(f"Error: {csv_export_path} not found")
        return

    # Figma API endpoints
    base_url = "https://api.figma.com/v1"
    headers = {"X-Figma-Token": figma_token}

    # Read CSV content
    with open(csv_export_path, "r") as f:
        csv_content = f.read()

    # Prepare Figma API payload (as text node)
    payload = {
        "type": "TEXT",
        "characters": csv_content,
        "style": {"fontFamily": "Roboto", "fontSize": 12},
    }

    # Find the node ID for the KPI Table page
    file_url = f"{base_url}/files/{figma_file_key}"
    resp = requests.get(file_url, headers=headers, timeout=30)
    resp.raise_for_status()
    file_data = resp.json()

    page_node_id = None
    for child in file_data["document"]["children"]:
        if child.get("name") == figma_page_name:
            page_node_id = child.get("id")
            break

    if not page_node_id:
        raise ValueError(f"Page '{figma_page_name}' not found in Figma file.")

    update_url = f"{base_url}/files/{figma_file_key}/nodes?ids={page_node_id}"
    update_resp = requests.put(
        update_url, headers=headers, data=json.dumps(payload), timeout=30
    )
    update_resp.raise_for_status()
    print(f"KPI table synced to Figma at {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
