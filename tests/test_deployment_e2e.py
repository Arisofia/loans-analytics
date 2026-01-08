import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.run_data_pipeline import main as pipeline_main
from src.pipeline.orchestrator import UnifiedPipeline


class TestDeploymentE2E:
    """End-to-end tests verifying production-ready deployment state."""
    
    @pytest.fixture
    def sample_dataset(self, tmp_path):
        """Create minimal sample dataset for testing."""
        df = pd.DataFrame({
            "segment": ["Consumer", "Consumer", "SME", "SME"],
            "measurement_date": ["2025-01-31"] * 4,
            "total_receivable_usd": [250000, 300000, 500000, 450000],
            "total_eligible_usd": [250000, 300000, 500000, 450000],
            "cash_available_usd": [245000, 294000, 490000, 432000],
            "dpd_0_7_usd": [5000, 6000, 10000, 18000],
            "dpd_7_30_usd": [0, 0, 0, 0],
            "dpd_30_60_usd": [0, 0, 0, 0],
            "dpd_60_90_usd": [0, 0, 0, 0],
            "dpd_90_plus_usd": [0, 0, 0, 0],
            "discounted_balance_usd": [250000, 300000, 500000, 450000],
        })
        dataset_file = tmp_path / "input.csv"
        df.to_csv(dataset_file, index=False)
        return dataset_file
    
    def test_e2e_pipeline_execution_produces_valid_output(self, sample_dataset, minimal_config_path):
        """Test that full pipeline execution produces complete, valid output."""
        pipeline = UnifiedPipeline(config_path=Path(minimal_config_path))
        summary = pipeline.execute(sample_dataset)
        
        assert summary["status"] == "success"
        run_id = summary["run_id"]
        
        # Verify artifacts exist
        run_dir = Path("logs/runs") / run_id
        assert run_dir.exists()
        assert (run_dir / f"{run_id}_summary.json").exists()
        assert (run_dir / f"{run_id}_compliance.json").exists()
        
        # Verify manifest
        manifest_path = Path(summary["phases"]["output"]["manifest"])
        assert manifest_path.exists()
        
        with open(manifest_path) as f:
            manifest = json.load(f)
            
        assert "metrics" in manifest
        metrics = manifest["metrics"]
        assert "PAR30" in metrics
        assert "CollectionRate" in metrics
    
    def test_e2e_main_script_success(self, sample_dataset, minimal_config_path):
        """Test complete pipeline execution through scripts/run_data_pipeline.py."""
        success = pipeline_main(
            input_file=str(sample_dataset),
            config_path=str(minimal_config_path)
        )
        assert success is True
    
    def test_e2e_missing_dataset_error(self, tmp_path, minimal_config_path):
        """Test pipeline returns error for missing dataset."""
        nonexistent_file = tmp_path / "nonexistent.csv"
        
        success = pipeline_main(
            input_file=str(nonexistent_file),
            config_path=str(minimal_config_path)
        )
        assert success is False
