import os
import requests
import json


FIGMA_FILE_ID = "nuVKwuPuLS7VmLFvqzOX1G"
FIGMA_TOKEN = os.environ.get("FIGMA_TOKEN")
FIGMA_API_URL = os.environ.get("FIGMA_API_URL")

if FIGMA_API_URL:
    # Use MCP server endpoint
    import requests.exceptions
    payload = {"file_id": FIGMA_FILE_ID}
    try:
        response = requests.post(f"{FIGMA_API_URL}/figma/file", json=payload, timeout=30)
        data = response.json()
    except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        print(f"Error: HTTP request to MCP server timed out or failed: {e}")
        data = {}
else:
    # Use direct Figma API
    import requests.exceptions
    headers = {"X-Figma-Token": FIGMA_TOKEN}
    url = f"https://api.figma.com/v1/files/{FIGMA_FILE_ID}"
    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
    except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        print(f"Error: HTTP request to Figma API timed out or failed: {e}")
        data = {}

# Save the file data to a local JSON for inspection
output_path = "exports/presentation/figma_file_data.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Figma file data exported to {output_path}")
