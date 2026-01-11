import os
import re

# Path to your coverage report
COVERAGE_REPORT = "coverage_report.txt"
# Minimum coverage percent to flag
THRESHOLD = 60
# Where to create test stubs (customize as needed)
TESTS_DIR = "tests/unit"

if not os.path.exists(TESTS_DIR):
    os.makedirs(TESTS_DIR)

stub_template = '''import pytest

def test_placeholder():
    assert True
'''

files_created = []

with open(COVERAGE_REPORT) as f:
    lines = f.readlines()

# Pattern matches lines in the coverage report for source files
pattern = re.compile(r'^(\S.+?\.py)\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%')

for line in lines:
    match = pattern.match(line)
    if match:
        filename, percent = match.groups()
        percent = int(percent)
        if percent < THRESHOLD and 'test' not in filename:
            # Build stub test file path
            base = os.path.basename(filename).replace('.py', '')
            # test_<corefilename>_stub.py
            test_stub_name = f"test_{base}_stub.py"
            test_stub_path = os.path.join(TESTS_DIR, test_stub_name)
            if not os.path.exists(test_stub_path):
                with open(test_stub_path, "w") as f:
                    f.write(stub_template)
                files_created.append(test_stub_path)

if files_created:
    print("Created test stubs for files with low coverage:")
    for f in files_created:
        print(" -", f)
else:
    print("No new stubs created. All files are above threshold or already have a test stub.")
