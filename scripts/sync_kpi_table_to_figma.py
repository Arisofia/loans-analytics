import json
import os
from datetime import datetime

import requests

# Figma API settings
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
FIGMA_FILE_KEY = os.getenv("FIGMA_FILE_KEY")
if not FIGMA_TOKEN or not FIGMA_FILE_KEY:
    raise RuntimeError("FIGMA_TOKEN and FIGMA_FILE_KEY must be set before syncing to Figma")
FIGMA_PAGE_NAME = "KPI Table"
CSV_EXPORT_PATH = "exports/KPI_Mapping_Table.csv"

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
resp = requests.get(file_url, headers=HEADERS)
resp.raise_for_status()
file_data = resp.json()

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
update_resp = requests.put(update_url, headers=HEADERS, data=json.dumps(payload))
update_resp.raise_for_status()
print(f"KPI table synced to Figma at {datetime.now().isoformat()}")
