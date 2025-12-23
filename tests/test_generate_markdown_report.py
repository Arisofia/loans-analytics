import os
import tempfile
import unittest
from pathlib import Path

from scripts.generate_markdown_report import generate_report


class TestGenerateMarkdownReport(unittest.TestCase):
    def test_generate_report_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            text_out = tmp_path / "out.txt"
            text_out.write_text("Some analysis")

            img_out = tmp_path / "plot.png"
            img_out.touch()

            report_out = tmp_path / "report.md"

            generate_report(str(report_out), str(text_out), [str(img_out)])

            self.assertTrue(report_out.exists())
            content = report_out.read_text(encoding="utf-8")
            self.assertIn("Some analysis", content)
            self.assertIn("plot.png", content)

    def test_generate_report_handles_missing_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            report_out = tmp_path / "report.md"

            generate_report(str(report_out), "missing.txt", ["missing.png"])

            self.assertTrue(report_out.exists())
            content = report_out.read_text(encoding="utf-8")
            self.assertIn("Text output file not found", content)
            self.assertIn("No visualizations generated", content)
