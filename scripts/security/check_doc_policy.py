import sys
from pathlib import Path

# Policy: Only one authoritative README per directory, no duplicates, no stale/example/sample config files


def main(doc_list_file):
    with open(doc_list_file) as f:
        files = [line.strip() for line in f if line.strip()]

    readme_map = {}
    violations = []

    for file in files:
        p = Path(file)
        if p.name.lower().startswith("readme"):
            dir_key = str(p.parent.resolve())
            readme_map.setdefault(dir_key, []).append(p)
        if any(x in p.name.lower() for x in ["example", "sample", "copy", "placeholder"]):
            violations.append(f"Stale/example config: {file}")

    for dir_key, readmes in readme_map.items():
        if len(readmes) > 1:
            violations.append(f"Duplicate READMEs in {dir_key}: {[str(r) for r in readmes]}")

    if violations:
        print("\nPOLICY VIOLATIONS DETECTED:")
        for v in violations:
            print(f"- {v}")
        sys.exit(1)
    else:
        print("No documentation/config policy violations found.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_doc_policy.py <doc_list_file>")
        sys.exit(2)
    main(sys.argv[1])
