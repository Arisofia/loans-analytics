import json
import sys
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config.paths import Paths
from src.config.secrets import get_secrets_manager

# Secrets
secrets = get_secrets_manager()
FIGMA_TOKEN = secrets.get("FIGMA_TOKEN", required=True)
FIGMA_FILE_KEY = secrets.get("FIGMA_FILE_KEY", required=True)

# Paths
FIGMA_PAGE_NAME = "KPI Table"
CSV_EXPORT_PATH = Paths.exports_dir() / "KPI_Mapping_Table.csv"

# Figma API endpoints
BASE_URL = "https://api.figma.com/v1"
HEADERS = {"X-Figma-Token": FIGMA_TOKEN}

# Read CSV content
with open(CSV_EXPORT_PATH, "r") as f:
    csv_content = f.read()

# Prepare Figma API payload (as text node)
payload = {
    "type": "TEXT",
    "characters": csv_content,
    "style": {"fontFamily": "Roboto", "fontSize": 12},
}

# Find the node ID for the KPI Table page

file_url = f"{BASE_URL}/files/{FIGMA_FILE_KEY}"
try:
    resp = requests.get(file_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    file_data = resp.json()
except requests.exceptions.Timeout:
    raise RuntimeError("Figma API request timed out.")
except requests.exceptions.RequestException as e:
    raise RuntimeError(f"Figma API request failed: {e}")

page_node_id = None
for child in file_data["document"]["children"]:
    if child["name"] == FIGMA_PAGE_NAME:
        page_node_id = child["id"]
        break
if not page_node_id:
    raise ValueError(f"Page '{FIGMA_PAGE_NAME}' not found in Figma file.")

# Update the text node (requires Figma plugin or automation)
# This is a placeholder for actual Figma API update logic

update_url = f"{BASE_URL}/files/{FIGMA_FILE_KEY}/nodes?ids={page_node_id}"
try:
    update_resp = requests.put(update_url, headers=HEADERS, data=json.dumps(payload), timeout=30)
    update_resp.raise_for_status()
    print(f"KPI table synced to Figma at {datetime.now().isoformat()}")
except requests.exceptions.Timeout:
    raise RuntimeError("Figma API update request timed out.")
except requests.exceptions.RequestException as e:
    raise RuntimeError(f"Figma API update request failed: {e}")
