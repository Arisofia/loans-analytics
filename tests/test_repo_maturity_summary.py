import unittest
import tempfile
from pathlib import Path
import os
import sys

# Ensure root is in path to import repo_maturity_summary
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.repo_maturity_summary import determine_level, LEVEL_CRITERIA

class TestRepoMaturitySummary(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_structure(self, items):
        for item in items:
            path = self.base_path / item
            if item.endswith("/"):
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

    def test_level_0_empty_repo(self):
        """Test that an empty repo returns level 0."""
        level = determine_level(self.base_path)
        self.assertEqual(level, 0)

    def test_level_1_readme_only(self):
        """Test that having just a README returns level 1."""
        self.create_structure(["README.md"])
        level = determine_level(self.base_path)
        self.assertEqual(level, 1)

    def test_level_2_basic_structure(self):
        """Test that README + requirements + tests/ returns level 2."""
        self.create_structure(["README.md", "requirements.txt", "tests/"])
        level = determine_level(self.base_path)
        self.assertEqual(level, 2)

    def test_level_3_docs_and_workflows(self):
        """Test that adding docs/ and workflows/ reaches level 3."""
        self.create_structure(["README.md", "requirements.txt", "tests/", ".github/workflows/", "docs/"])
        level = determine_level(self.base_path)
        self.assertEqual(level, 3)

    def test_level_4_full_maturity(self):
        """Test that adding Dockerfile and Sonar config reaches level 4."""
        self.create_structure(["README.md", "requirements.txt", "tests/", ".github/workflows/", "docs/", "Dockerfile", "sonar-project.properties"])
        level = determine_level(self.base_path)
        self.assertEqual(level, 4)