import os
from datetime import datetime

# Paths
KPI_MD_PATH = "docs/analytics/KPIs.md"
EXPORTS_DIR = "exports"
CSV_EXPORT_PATH = os.path.join(EXPORTS_DIR, "KPI_Mapping_Table.csv")

# Ensure exports directory exists
os.makedirs(EXPORTS_DIR, exist_ok=True)

# Convert Markdown table to CSV

def md_table_to_csv(md_path, csv_path):
    with open(md_path, "r") as f:
        lines = f.readlines()
    # Find the KPI Mapping Table header
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("| KPI Name"):
            start = i
            break
    if start is None:
        raise ValueError("KPI Mapping Table not found in markdown file.")
    # Collect table lines
    table_lines = []
    for line in lines[start:]:
        if not line.strip().startswith("|"):
            break
        table_lines.append(line.strip())
    # Convert to CSV
    with open(csv_path, "w") as f:
        for line in [l for l in table_lines if '---' not in l]:
            row = [col.strip() for col in line.strip("|").split("|")]
            f.write(",".join(row) + "\n")
    print(f"Exported KPI table to {csv_path}")

if __name__ == "__main__":
    md_table_to_csv(KPI_MD_PATH, CSV_EXPORT_PATH)
    # Optionally, add timestamp or sync logic for Figma API integration
    print(f"KPI table export completed at {datetime.now().isoformat()}")
