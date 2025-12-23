import requests
import os
import json
from datetime import datetime

# Figma API settings
FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
FIGMA_FILE_KEY = os.getenv("FIGMA_FILE_KEY")
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
    "style": {
        "fontFamily": "Roboto",
        "fontSize": 12
    }
}

# Find the node ID for the KPI Table page
file_url = f"{BASE_URL}/files/{FIGMA_FILE_KEY}"
import requests.exceptions
try:
    resp = requests.get(file_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    file_data = resp.json()
except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
    print(f"Error: HTTP request to Figma API timed out or failed: {e}")
    file_data = {}

page_node_id = None
for child in file_data["document"]["children"]:
    if child.get("name") == FIGMA_PAGE_NAME:
        page_node_id = child.get("id")
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
except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
    print(f"Error: HTTP request to update Figma node timed out or failed: {e}")
