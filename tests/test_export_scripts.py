import json
import tempfile
import unittest
from pathlib import Path

from scripts.export_copilot_slide_payload import export_payload


class TestExportScripts(unittest.TestCase):
    def test_export_copilot_slide_payload(self):
        """Test that the slide payload export generates valid JSON with required fields."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            output_dir = Path(tmpdirname)
            json_path = export_payload(output_dir)

            self.assertTrue(json_path.exists())
            self.assertEqual(json_path.name, "copilot-slide-payload.json")

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("theme", data)
            self.assertIn("slides", data)
            self.assertIsInstance(data["slides"], list)
            self.assertTrue(len(data["slides"]) > 0)
