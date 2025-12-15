"""
repo_maturity_summary.py

Analyzes the repository for maturity level and generates a summary report.
"""
import os
from pathlib import Path


# Constants for repeated string literals
README = "README.md"
REQUIREMENTS = "requirements.txt"
TESTS_DIR = "tests/"
WORKFLOWS_DIR = ".github/workflows/"
DOCS_DIR = "docs/"
DOCKERFILE = "Dockerfile"
SONAR = "sonar-project.properties"

LEVEL_CRITERIA = {
    1: [README],
    2: [README, REQUIREMENTS, TESTS_DIR],
    3: [README, REQUIREMENTS, TESTS_DIR, WORKFLOWS_DIR, DOCS_DIR],
    4: [README, REQUIREMENTS, TESTS_DIR, WORKFLOWS_DIR, DOCS_DIR, DOCKERFILE, SONAR],
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
    LEVEL_MSG = "Repository maturity level: {}"
    CRITERIA_MET_MSG = "Criteria met:"
    NEXT_LEVEL_MSG = "\nFor next level, add:"
    ALL_MET_MSG = "- All criteria met for highest level."
    print(LEVEL_MSG.format(level))
    print(CRITERIA_MET_MSG)
    for item in LEVEL_CRITERIA.get(level, []):
        print(f"- {item}")
    print(NEXT_LEVEL_MSG)
    next_level = level + 1
    if next_level in LEVEL_CRITERIA:
        missing = [item for item in LEVEL_CRITERIA[next_level] if not (base_path / item).exists() and not (base_path / item[:-1]).is_dir()]
        for item in missing:
            print(f"- {item}")
    else:
        print(ALL_MET_MSG)

if __name__ == "__main__":
    main()