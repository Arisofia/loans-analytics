import logging
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from .ingestion import UnifiedIngestion
from .transformation import UnifiedTransformation
from .calculation import UnifiedCalculation
from .output import UnifiedOutput

logger = logging.getLogger(__name__)

class UnifiedPipeline:
    """The ONE canonical orchestrator for the Abaco Data Pipeline."""

    def __init__(self, config_path: str = "config/pipeline.yml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize Phases
        self.ph1_ingestion = UnifiedIngestion(self.config)
        self.ph2_transformation = UnifiedTransformation(self.config)
        self.ph3_calculation = UnifiedCalculation(self.config)
        self.ph4_output = UnifiedOutput(self.config)

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Pipeline config not found: {self.config_path}")
        with self.config_path.open("r") as f:
            return yaml.safe_load(f)

    def run(self, input_file: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the end-to-end canonical pipeline."""
        context = context or {"user": "system", "action": "batch_process"}
        logger.info(f"Starting Unified Pipeline Run | input={input_file} | context={context}")

        try:
            # Phase 1: Ingestion
            ingest_res = self.ph1_ingestion.ingest_file(Path(input_file))
            
            # Phase 2: Transformation
            tx_res = self.ph2_transformation.transform(ingest_res.df)
            
            # Phase 3: Calculation
            calc_res = self.ph3_calculation.calculate(tx_res.df)
            
            # Phase 4: Output & Distribution
            run_ids = {
                "ingest": ingest_res.run_id,
                "transform": tx_res.run_id,
                "calculate": calc_res.run_id
            }
            
            metadata = {
                "input_context": context,
                "ingestion": ingest_res.metadata,
                "lineage": tx_res.lineage,
                "audit_trail": calc_res.audit_trail
            }
            
            manifest = self.ph4_output.persist(
                tx_res.df, 
                calc_res.metrics, 
                metadata, 
                run_ids
            )
            
            logger.info(f"Unified Pipeline Completed Successfully | run_id={ingest_res.run_id}")
            return manifest

        except Exception as e:
            logger.exception(f"Pipeline failed at phase: {type(e).__name__}: {e}")
            raise
