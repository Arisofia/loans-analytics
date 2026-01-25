import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config.paths import Paths

# Paths
KPI_MD_PATH = Paths.docs_dir() / "analytics/KPIs.md"
EXPORTS_DIR = Paths.exports_dir(create=True)
CSV_EXPORT_PATH = EXPORTS_DIR / "KPI_Mapping_Table.csv"

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
        if "---" not in line:
            table_lines.append(line.strip())
    # Convert to CSV
    with open(csv_path, "w") as f:
        for line in [row_line for row_line in table_lines if "---" not in row_line]:
            row = [col.strip() for col in line.strip("|").split("|")]
            f.write(",".join(row) + "\n")
    print(f"Exported KPI table to {csv_path}")


if __name__ == "__main__":
    md_table_to_csv(KPI_MD_PATH, CSV_EXPORT_PATH)
    # Optionally, add timestamp or sync logic for Figma API integration
    print(f"KPI table export completed at {datetime.now().isoformat()}")
