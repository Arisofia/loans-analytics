"""
Script to validate that all field references in KPI formulas exist in the specified data sources.
- Loads KPI definitions and data source schemas from YAML.
- Parses each formula for field references (e.g., sum(field), count(field), field).
- Checks that each referenced field exists in at least one of the specified data sources.
- Prints errors for missing fields.
"""
import re
import sys
import yaml
from pathlib import Path

KPI_DEFINITIONS_PATH = Path("config/kpi_definitions.yml")
DATA_SOURCE_SCHEMAS_PATH = Path("config/data_source_schemas.yml")

FIELD_PATTERN = re.compile(r"(?:sum|count|avg|min|max)\((\w+)\)|\b(\w+)\b")


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def extract_fields(formula):
    # Find all field references in the formula
    fields = set()
    for match in FIELD_PATTERN.finditer(formula):
        if match.group(1):
            fields.add(match.group(1))
        elif match.group(2):
            # Exclude function names and numbers
            if not match.group(2).isdigit() and match.group(2) not in {"sum", "count", "avg", "min", "max"}:
                fields.add(match.group(2))
    return fields

def main():
    kpis = load_yaml(KPI_DEFINITIONS_PATH)
    schemas = load_yaml(DATA_SOURCE_SCHEMAS_PATH)
    errors = []
    for kpi_key, kpi in kpis.items():
        formula = kpi.get("formula", "")
        data_sources = kpi.get("data_sources", [])
        if not formula or not data_sources:
            continue
        fields = extract_fields(formula)
        available_fields = set()
        for ds in data_sources:
            available_fields.update(schemas.get(ds, []))
        missing = fields - available_fields
        if missing:
            errors.append(f"KPI '{kpi_key}' formula references missing fields: {sorted(missing)} (data_sources: {data_sources})")
    if errors:
        print("Field reference validation errors found:")
        for err in errors:
            print("-", err)
        sys.exit(1)
    else:
        print("All KPI formula field references are valid.")

if __name__ == "__main__":
    main()
