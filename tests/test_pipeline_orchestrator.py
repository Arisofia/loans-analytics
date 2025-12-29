import pytest
from pathlib import Path
import tempfile
import pandas as pd
from python.pipeline.orchestrator import UnifiedPipeline, PipelineConfig


class TestPipelineConfig:
    def test_config_defaults(self):
        config = PipelineConfig(config_path=Path("nonexistent.yml"))
        
        assert config.config["name"] == "abaco_unified_pipeline"
        assert "pipeline" in config.config
        assert "phases" in config.config["pipeline"]

    def test_config_validation(self):
        invalid_config = {"name": "test"}
        with pytest.raises(ValueError):
            config = PipelineConfig()
            config.config = invalid_config
            config._validate_config()

    def test_config_get_method(self):
        config = PipelineConfig(config_path=Path("nonexistent.yml"))
        
        name = config.get("name")
        assert name == "abaco_unified_pipeline"
        
        pipeline = config.get("pipeline", "phases", "ingestion")
        assert pipeline is not None


class TestUnifiedPipeline:
    @pytest.fixture
    def sample_csv_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                "loan_id": ["loan_1", "loan_2", "loan_3"],
                "total_receivable_usd": [1000, 2000, 500],
                "dpd_0_7_usd": [0, 0, 0],
                "dpd_7_30_usd": [0, 0, 0],
                "dpd_30_60_usd": [100, 200, 0],
                "dpd_60_90_usd": [50, 100, 0],
                "dpd_90_plus_usd": [25, 50, 0],
                "total_eligible_usd": [1000, 2000, 500],
                "cash_available_usd": [100, 200, 50],
            })
            df.to_csv(f, index=False)
            return Path(f.name)

    def test_pipeline_initialization(self):
        pipeline = UnifiedPipeline(config_path=Path("nonexistent.yml"))
        assert pipeline.run_id is not None
        assert "pipeline_" in pipeline.run_id

    def test_pipeline_execute(self, sample_csv_file):
        pipeline = UnifiedPipeline(config_path=Path("nonexistent.yml"))
        result = pipeline.execute(sample_csv_file)
        
        assert "status" in result
        assert "run_id" in result
        if result["status"] == "success":
            assert "phases" in result
