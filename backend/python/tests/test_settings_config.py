"""Tests for repository-backed settings loading."""

import tempfile
import unittest
from pathlib import Path

from backend.python.config import Settings


class TestSettingsConfig(unittest.TestCase):
    """Validate canonical guardrail loading from repository config files."""

    def test_load_settings_uses_business_rules_when_business_parameters_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "business_rules.yaml").write_text(
                """
guardrails:
  target_rotation: 6.2
  max_default_rate: 0.07
  max_top_10_concentration: 0.22
  max_single_obligor: 0.03
  target_apr_min: 0.31
  target_apr_max: 0.42
  min_dscr: 1.4
  min_collection_efficiency_6m: 0.91
                """.strip(),
                encoding="utf-8",
            )

            loaded = Settings.load_settings(project_root=root)

            self.assertEqual(loaded.financial.min_rotation, 6.2)
            self.assertEqual(loaded.financial.max_default_rate, 0.07)
            self.assertEqual(loaded.financial.max_top_10_concentration, 0.22)
            self.assertEqual(loaded.financial.max_single_obligor_concentration, 0.03)
            self.assertEqual(loaded.financial.min_dscr, 1.4)
            self.assertEqual(loaded.financial.min_ce_6m, 0.91)

    def test_business_parameters_override_business_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "business_rules.yaml").write_text(
                "guardrails:\n  target_rotation: 5.0\n",
                encoding="utf-8",
            )
            (config_dir / "business_parameters.yml").write_text(
                "financial_guardrails:\n  min_rotation: 7.5\n",
                encoding="utf-8",
            )

            loaded = Settings.load_settings(project_root=root)

            self.assertEqual(loaded.financial.min_rotation, 7.5)


if __name__ == "__main__":
    unittest.main()
