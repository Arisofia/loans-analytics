# validate_kpi_formulas.py
"""
Validates that all field references in KPI formulas exist in the declared data source schemas.
Usage: python validate_kpi_formulas.py config/kpi_definitions.yml
"""
import re
import sys

import yaml

FIELD_PATTERN = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b")

IGNORED_WORDS = {
    "sum",
    "count",
    "min",
    "max",
    "mean",
    "avg",
    "if",
    "else",
    "and",
    "or",
    "not",
    "null",
    "None",
    "True",
    "False",
    "int",
    "float",
    "str",
    "abs",
    "round",
    "len",
    "in",
    "for",
    "return",
    "def",
    "lambda",
    "import",
    "as",
    "from",
}


def extract_fields(formula):
    # Extract all variable-like tokens, filter out known functions/keywords
    tokens = set(FIELD_PATTERN.findall(formula))
    return {t for t in tokens if t not in IGNORED_WORDS and not t.isdigit()}


def main(yaml_path):
    with open(yaml_path) as f:
        config = yaml.safe_load(f)

    schemas = config.get("schemas", {})
    errors = []

    for kpi_key, kpi in config.items():
        if kpi_key == "schemas" or not isinstance(kpi, dict):
            continue
        formula = kpi.get("formula")
        data_sources = kpi.get("data_sources", [])
        if not formula or not data_sources:
            continue
        fields = extract_fields(formula)
        # Build set of all available fields from declared sources
        available_fields = set()
        for src in data_sources:
            available_fields.update(schemas.get(src, []))
        # Check for missing fields
        missing = fields - available_fields
        if missing:
            errors.append(
                f"KPI '{kpi_key}' references missing fields: {sorted(missing)} (sources: {data_sources})"
            )

    if errors:
        print("Validation failed! The following issues were found:")
        for err in errors:
            print("-", err)
        sys.exit(1)
    else:
        print("All KPI formulas reference valid fields.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_kpi_formulas.py <kpi_definitions.yml>")
        sys.exit(2)
    main(sys.argv[1])
