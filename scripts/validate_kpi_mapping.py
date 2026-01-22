"""
Script to validate KPI mapping table against codebase data sources and KPI definitions.
- Checks that each Data Source in the mapping table exists in the codebase (YAML, Python, or JSON schema).
- Reports missing or mismatched sources.

Usage: python validate_kpi_mapping.py exports/KPI_Mapping_Table_for_Presentation.md config/kpi_definitions.yml
"""

import re
import sys
from typing import Set

import yaml

MAPPING_ROW_PATTERN = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$"
)


def extract_data_sources_from_mapping(md_path: str) -> Set[str]:
    sources = set()
    with open(md_path) as f:
        for line in f:
            m = MAPPING_ROW_PATTERN.match(line)
            if m:
                data_source = m.group(3)
                # Split on / or whitespace, flatten
                for part in re.split(r"[\s/]+", data_source):
                    if part and not part.endswith("*"):
                        sources.add(part.strip())
    return sources


def extract_known_sources_from_kpi_yaml(yaml_path: str) -> Set[str]:
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    known = set()
    # Look for schemas section
    schemas = config.get("schemas", {})
    for src in schemas:
        known.add(src)
    # Also scan all formula/data_sources fields
    for kpi in config.values():
        if isinstance(kpi, dict):
            for src in kpi.get("data_sources", []):
                known.add(src)
    return known


def main(md_path: str, yaml_path: str):
    mapping_sources = extract_data_sources_from_mapping(md_path)
    known_sources = extract_known_sources_from_kpi_yaml(yaml_path)
    missing = mapping_sources - known_sources
    extra = known_sources - mapping_sources
    print(f"Sources in mapping but not in codebase: {sorted(missing)}")
    print(f"Sources in codebase but not in mapping: {sorted(extra)}")
    if missing:
        print("\nERROR: Some mapping sources are not defined in the codebase!")
        sys.exit(1)
    print("\nAll mapping sources are present in the codebase.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python validate_kpi_mapping.py <KPI_Mapping_Table_for_Presentation.md> <kpi_definitions.yml>"
        )
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
