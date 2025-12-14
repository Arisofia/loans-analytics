"""
repo_maturity_summary.py

Analyzes the repository for maturity level and generates a summary report.
"""
import os
import yaml
from pathlib import Path

LEVEL_CRITERIA = {
    1: ["README.md"],
    2: ["README.md", "requirements.txt", "tests/"],
    3: ["README.md", "requirements.txt", "tests/", ".github/workflows/", "docs/"],
    4: ["README.md", "requirements.txt", "tests/", ".github/workflows/", "docs/", "Dockerfile", "sonar-project.properties"],
}

def check_criteria(base_path, criteria):
    for item in criteria:
        if item.endswith("/"):
            if not (base_path / item[:-1]).is_dir():
                return False
        else:
            if not (base_path / item).exists():
                return False
    return True

def determine_level(base_path):
    for level in sorted(LEVEL_CRITERIA.keys(), reverse=True):
        if check_criteria(base_path, LEVEL_CRITERIA[level]):
            return level
    return 0

def main():
    base_path = Path(os.getcwd())
    level = determine_level(base_path)
    print(f"Repository maturity level: {level}")
    print("Criteria met:")
    for item in LEVEL_CRITERIA.get(level, []):
        print(f"- {item}")
    print("\nFor next level, add:")
    next_level = level + 1
    if next_level in LEVEL_CRITERIA:
        missing = [item for item in LEVEL_CRITERIA[next_level] if not (base_path / item).exists() and not (base_path / item[:-1]).is_dir()]
        for item in missing:
            print(f"- {item}")
    else:
        print("- All criteria met for highest level.")

if __name__ == "__main__":
    main()
