import os
import requests
import json

FIGMA_FILE_ID = "nuVKwuPuLS7VmLFvqzOX1G"
FIGMA_TOKEN = os.environ.get("FIGMA_TOKEN")

headers = {
    "X-Figma-Token": FIGMA_TOKEN
}

url = f"https://api.figma.com/v1/files/{FIGMA_FILE_ID}"
response = requests.get(url, headers=headers)
data = response.json()

# Save the file data to a local JSON for inspection
output_path = "exports/presentation/figma_file_data.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    json.dump(data, f, indent=2)

print(f"Figma file data exported to {output_path}")
