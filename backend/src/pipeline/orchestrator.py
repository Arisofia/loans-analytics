import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from backend.loans_analytics.logging_config import get_logger
from .calculation import CalculationPhase
from .config import PipelineConfig, load_business_rules, load_kpi_definitions
from .ingestion import IngestionPhase
from .output import OutputPhase
from .transformation import TransformationPhase
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Decision Intelligence imports
from backend.src.pipeline.decision_phase import DecisionPhase
from backend.src.pipeline.constants import GSHEETS_URI_PREFIX
OTEL_AVAILABLE = True
logger = get_logger(__name__)
PIPELINE_STATUS_ATTR = 'pipeline.status'
PIPELINE_DURATION_ATTR = 'pipeline.duration_seconds'

class UnifiedPipeline:
    _GSHEETS_URI_PREFIX = GSHEETS_URI_PREFIX

    def __init__(self, config_path: Optional[Path]=None, base_log_dir: Optional[Path]=None):
        logger.info('%s', '=' * 80)
        logger.info('UNIFIED PIPELINE ORCHESTRATOR v2.0')
        logger.info('%s', '=' * 80)
        self.config = PipelineConfig.load(config_path)
        self.business_rules = load_business_rules()
        self.kpi_definitions = load_kpi_definitions()
        self.base_log_dir = base_log_dir or Path('logs') / 'runs'
        self.enable_tracing = os.getenv('PIPELINE_TRACING_ENABLED', '1') == '1' and OTEL_AVAILABLE
        self._tracer = trace.get_tracer(__name__) if self.enable_tracing else None
        self.ingestion = IngestionPhase(self.config.ingestion)
        self.transformation = TransformationPhase(self.config.transformation, self.business_rules)
        self.calculation = CalculationPhase(self.config.calculation, self.kpi_definitions)
        self.output = OutputPhase(self.config.output)
        self.decision = DecisionPhase()
        logger.info('All pipeline phases initialized successfully')

    def _start_span(self, name: str, attributes: Optional[Dict[str, Any]]=None):
        if self._tracer is None:
            return nullcontext(None)
        return self._tracer.start_as_current_span(name, attributes=attributes or {})

    def _execute_phase(self, *, phase_name: str, run_id: str, executor: Any, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        with self._start_span(f'pipeline.{phase_name}', {'pipeline.run_id': run_id, 'pipeline.phase': phase_name}) as phase_span:
            started = time.perf_counter()
            try:
                phase_results = executor(**kwargs)
            except Exception as exc:
                if phase_span is not None:
                    phase_span.record_exception(exc)
                    phase_span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise
            duration = round(time.perf_counter() - started, 6)
            phase_results['duration_seconds'] = duration
            if phase_span is not None:
                phase_status = str(phase_results.get('status', 'unknown'))
                phase_span.set_attribute('pipeline.phase.status', phase_status)
                phase_span.set_attribute('pipeline.phase.duration_seconds', duration)
                if phase_status == 'success':
                    phase_span.set_status(Status(StatusCode.OK))
                else:
                    phase_span.set_status(Status(StatusCode.ERROR, str(phase_results.get('error', 'phase_failed'))))
            return phase_results

    def _build_run_id(self, input_path: Optional[Path], mode: str) -> str:
        mode_token = mode.replace('-', '_')
        if input_path is not None:
            if self._is_google_sheets_uri(input_path):
                data_hash = self._calculate_ingestion_source_hash(str(input_path))
            else:
                if not input_path.exists():
                    raise FileNotFoundError(f'Input file not found: {input_path}')
                data_hash = self._calculate_input_hash(input_path)
        else:
            data_hash = self._calculate_ingestion_source_hash()
        config_hash = self._calculate_config_hash()
        code_version = self._get_code_version()
        run_signature = self._calculate_run_signature(data_hash, config_hash, code_version, mode_token)
        base_run_id = run_signature[:16]
        return base_run_id if mode == 'full' else f'{base_run_id}_{mode_token}'

    def _load_existing_run_results(self, run_dir: Path, run_id: str) -> Optional[Dict[str, Any]]:
        if not run_dir.exists():
            return None
        manifest_path = run_dir / 'pipeline_results.json'
        if not manifest_path.exists():
            return None
        logger.info('Run %s already exists, loading existing results (idempotent)', run_id)
        with open(manifest_path, 'r') as file_handle:
            return json.load(file_handle)

    @staticmethod
    def _record_phase_results(results: Dict[str, Any], phase_name: str, phase_results: Dict[str, Any]) -> None:
        results['phases'][phase_name] = phase_results
        results['phase_metrics'][phase_name] = {'status': phase_results.get('status'), 'duration_seconds': phase_results.get('duration_seconds', 0.0)}

    def _fail_on_phase_error(self, phase_name: str, phase_label: str, phase_results: Dict[str, Any]) -> None:
        if phase_results.get('status') == 'success':
            return
        raise RuntimeError(f"{phase_label} ({phase_name.title()}) failed: {phase_results.get('error')}")

    def _complete_early_mode(self, *, message: str, results: Dict[str, Any], run_dir: Path, pipeline_span: Any) -> Dict[str, Any]:
        logger.info(message)
        final_results = self._finalize_results(results, run_dir)
        self._finalize_pipeline_span(pipeline_span, final_results)
        return final_results

    @staticmethod
    def _finalize_pipeline_span(pipeline_span: Any, final_results: Optional[Dict[str, Any]]=None, exc: Optional[Exception]=None) -> None:
        if pipeline_span is None:
            return
        if final_results is not None:
            pipeline_span.set_attribute(PIPELINE_STATUS_ATTR, final_results['status'])
            pipeline_span.set_attribute(PIPELINE_DURATION_ATTR, final_results['duration_seconds'])
            status = StatusCode.OK if final_results['status'] == 'success' else StatusCode.ERROR
            description = None if status == StatusCode.OK else str(final_results.get('error', 'failed'))
            pipeline_span.set_status(Status(status, description))
            return
        if exc is not None:
            pipeline_span.record_exception(exc)
            pipeline_span.set_attribute(PIPELINE_STATUS_ATTR, 'error')
            pipeline_span.set_status(Status(StatusCode.ERROR, str(exc)))

    @staticmethod
    def _build_output_phase_kwargs(phase2_results: Dict[str, Any], phase3_results: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
        return {'kpi_results': phase3_results.get('kpis', {}), 'run_dir': run_dir, 'kpi_engine': phase3_results.get('kpi_engine'), 'segment_kpis': phase3_results.get('segment_kpis'), 'time_series': phase3_results.get('time_series'), 'anomalies': phase3_results.get('anomalies'), 'nsm_recurrent_tpv': phase3_results.get('nsm_recurrent_tpv'), 'clustering_metrics': phase3_results.get('clustering_metrics'), 'transformation_metrics': phase2_results.get('transformation_metrics'), 'expected_loss': phase3_results.get('expected_loss'), 'roll_rates': phase3_results.get('roll_rates'), 'vintage_analysis': phase3_results.get('vintage_analysis'), 'concentration_hhi': phase3_results.get('concentration_hhi')}

    def execute(self, input_path: Optional[Path]=None, mode: str='full') -> Dict[str, Any]:
        run_id = self._build_run_id(input_path, mode)
        logger.info('Starting pipeline execution (run_id: %s, mode: %s)', run_id, mode)
        run_dir = self.base_log_dir / run_id
        existing_results = self._load_existing_run_results(run_dir, run_id)
        if existing_results is not None:
            return existing_results
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info('Run directory: %s', run_dir)
        results: Dict[str, Any] = {'run_id': run_id, 'mode': mode, 'start_time': datetime.now().isoformat(), 'phases': {}, 'phase_metrics': {}}
        with self._start_span('pipeline.execute', {'pipeline.run_id': run_id, 'pipeline.mode': mode}) as pipeline_span:
            try:
                separator = '=' * 80
                logger.info('\n%s', separator)
                logger.info('PHASE 1: INGESTION')
                logger.info('%s', separator)
                phase1_results = self._execute_phase(phase_name='ingestion', run_id=run_id, executor=self.ingestion.execute, kwargs={'input_path': input_path, 'run_dir': run_dir})
                self._record_phase_results(results, 'ingestion', phase1_results)
                self._fail_on_phase_error('ingestion', 'Phase 1', phase1_results)
                if mode == 'dry-run':
                    return self._complete_early_mode(message='Dry-run mode: stopping after ingestion', results=results, run_dir=run_dir, pipeline_span=pipeline_span)
                logger.info('\n%s', separator)
                logger.info('PHASE 2: TRANSFORMATION')
                logger.info('%s', separator)
                raw_data_path = Path(phase1_results['output_path']) if phase1_results.get('output_path') else None
                phase2_results = self._execute_phase(phase_name='transformation', run_id=run_id, executor=self.transformation.execute, kwargs={'raw_data_path': raw_data_path, 'run_dir': run_dir})
                self._record_phase_results(results, 'transformation', phase2_results)
                self._fail_on_phase_error('transformation', 'Phase 2', phase2_results)
                if mode == 'validate':
                    return self._complete_early_mode(message='Validate mode: stopping after transformation', results=results, run_dir=run_dir, pipeline_span=pipeline_span)
                logger.info('\n%s', separator)
                logger.info('PHASE 3: CALCULATION')
                logger.info('%s', separator)
                clean_data_path = Path(phase2_results['output_path']) if phase2_results.get('output_path') else None
                phase3_results = self._execute_phase(phase_name='calculation', run_id=run_id, executor=self.calculation.execute, kwargs={'clean_data_path': clean_data_path})
                self._record_phase_results(results, 'calculation', phase3_results)
                self._fail_on_phase_error('calculation', 'Phase 3', phase3_results)
                logger.info('\n%s', separator)
                logger.info('PHASE 4: OUTPUT')
                logger.info('%s', separator)
                phase4_results = self._execute_phase(phase_name='output', run_id=run_id, executor=self.output.execute, kwargs=self._build_output_phase_kwargs(phase2_results, phase3_results, run_dir))
                self._record_phase_results(results, 'output', phase4_results)
                self._fail_on_phase_error('output', 'Phase 4', phase4_results)
                logger.info('\n%s', separator)
                logger.info('PHASE 5: DECISION INTELLIGENCE')
                logger.info('%s', separator)
                phase5_results = self._execute_phase(phase_name='decision', run_id=run_id, executor=self.decision.execute, kwargs={'phase2_results': phase2_results, 'phase3_results': phase3_results, 'business_rules': self.business_rules, 'run_dir': run_dir})
                self._record_phase_results(results, 'decision', phase5_results)
                if phase5_results.get('status') != 'success':
                    logger.warning('Phase 5 (Decision) finished with status: %s — non-blocking', phase5_results.get('status'))
                final_results = self._finalize_results(results, run_dir)
                self._finalize_pipeline_span(pipeline_span, final_results)
                return final_results
            except Exception as e:
                logger.error('Pipeline execution failed: %s', e)
                logger.error('%s', traceback.format_exc())
                results['status'] = 'failed'
                results['error'] = str(e)
                results['traceback'] = traceback.format_exc()
                final_results = self._finalize_results(results, run_dir)
                self._finalize_pipeline_span(pipeline_span, final_results, e)
                return final_results

    def _finalize_results(self, results: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
        results['end_time'] = datetime.now().isoformat()
        start = datetime.fromisoformat(results['start_time'])
        end = datetime.fromisoformat(results['end_time'])
        duration = (end - start).total_seconds()
        results['duration_seconds'] = duration
        if 'status' not in results:
            core_phases = {k: v for k, v in results['phases'].items() if k != 'decision'}
            all_success = all((phase.get('status') == 'success' for phase in core_phases.values()))
            results['status'] = 'success' if all_success else 'partial'
        manifest_path = run_dir / 'pipeline_results.json'
        with open(manifest_path, 'w') as f:
            json.dump(self._sanitize_json_keys(results), f, indent=2, default=str)
        separator = '=' * 80
        logger.info('\n%s', separator)
        logger.info('PIPELINE EXECUTION COMPLETE')
        logger.info('Status: %s', results['status'].upper())
        logger.info('Duration: %.2f seconds', duration)
        logger.info('Results: %s', manifest_path)
        return results

    @staticmethod
    def _sanitize_json_keys(obj: Any) -> Any:
        """Recursively convert non-str dict keys (e.g. numpy.int64) to str."""
        if isinstance(obj, dict):
            return {str(k): UnifiedPipeline._sanitize_json_keys(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [UnifiedPipeline._sanitize_json_keys(v) for v in obj]
        return obj

    @staticmethod
    def _calculate_input_hash(file_path: Path) -> str:
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as file_handle:
                while True:
                    chunk = file_handle.read(1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]
        except Exception as e:
            logger.error("Failed to hash input file '%s': %s", file_path, e, exc_info=True)
            raise RuntimeError(f"Failed to hash input file '{file_path}'") from e

    def _calculate_config_hash(self) -> str:
        try:
            config_str = json.dumps({'transformation': self.config.transformation, 'calculation': self.config.calculation, 'output': self.config.output}, sort_keys=True, default=str)
            return hashlib.sha256(config_str.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error('Failed to hash pipeline config', exc_info=True)
            raise RuntimeError('Unable to hash pipeline configuration deterministically') from e

    @staticmethod
    def _is_google_sheets_uri(path: Path) -> bool:
        normalized = str(path).replace('\\', '/')
        return normalized.startswith('gsheets://') or normalized.startswith('gsheets:/')

    def _calculate_ingestion_source_hash(self, source_hint: Optional[str]=None) -> str:
        try:
            ingestion_config = self.config.ingestion if isinstance(self.config.ingestion, dict) else {}
            canonical_ingestion = json.dumps(ingestion_config, sort_keys=True, default=str)
            source_component = str(source_hint or 'default')
            payload = f'ingestion_source|{source_component}|{canonical_ingestion}'
            return hashlib.sha256(payload.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error('Failed to hash ingestion source configuration', exc_info=True)
            raise RuntimeError('Unable to hash ingestion source deterministically') from e

    @staticmethod
    def _get_code_version() -> str:
        try:
            from backend.src.pipeline import __version__
            return __version__
        except Exception as exc:
            logger.debug('Falling back to pyproject.toml for code version', exc_info=exc)
        try:
            import tomllib
            repo_root = Path(__file__).resolve().parents[3]
            pyproject_path = repo_root / 'pyproject.toml'
            with open(pyproject_path, 'rb') as pyproject_file:
                pyproject = tomllib.load(pyproject_file)
            version = pyproject.get('project', {}).get('version')
            if isinstance(version, str) and version.strip():
                return version.strip()
        except Exception as exc:
            logger.debug('Unable to resolve code version from pyproject.toml', exc_info=exc)
        raise RuntimeError('Unable to resolve pipeline code version from backend.src.pipeline.__version__ or pyproject.toml')

    @staticmethod
    def _calculate_run_signature(data_hash: str, config_hash: str, code_version: str, mode: str) -> str:
        composite = '|'.join([data_hash, config_hash, code_version, mode])
        return hashlib.sha256(composite.encode()).hexdigest()[:16]

def main() -> int:
    parser = argparse.ArgumentParser(description='Unified 4-Phase Data Pipeline (Ingestion → Transformation → Calculation → Output)', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='Examples:\n  # Run full pipeline with a specific CSV input file\n  python scripts/data/run_data_pipeline.py --input /path/to/your/data.csv\n\n  # Live mode (alias for full - all 4 phases)\n  python scripts/data/run_data_pipeline.py --mode live --input data/samples/loans_sample_data_20260202.csv\n\n  # Validation mode (stop after transformation)\n  python scripts/data/run_data_pipeline.py --mode validate\n\n  # Dry-run mode (stop after ingestion)\n  python scripts/data/run_data_pipeline.py --mode dry-run\n\n  # Custom config file\n  python scripts/data/run_data_pipeline.py --config config/custom_pipeline.yml\n        ')
    parser.add_argument('--input', type=str, default=None, help='Path to input CSV file (optional, uses config default)')
    parser.add_argument('--config', type=str, default='config/pipeline.yml', help='Path to pipeline.yml config (default: config/pipeline.yml)')
    parser.add_argument('--mode', choices=['full', 'live', 'validate', 'dry-run'], default='full', help='Execution mode: full/live (all phases), validate (stop after transformation), dry-run (stop after ingestion)')
    args = parser.parse_args()
    try:
        config_path = Path(args.config) if args.config else None
        pipeline = UnifiedPipeline(config_path=config_path)
        input_path = Path(args.input) if args.input else None
        mode = 'full' if args.mode == 'live' else args.mode
        results = pipeline.execute(input_path=input_path, mode=mode)
        if results.get('status') == 'success':
            logger.info('✓ Pipeline completed successfully')
            return 0
        error_msg = results.get('error', 'Unknown error')
        logger.error('✗ Pipeline failed: %s', error_msg)
        return 1
    except Exception as e:
        logger.error('Fatal error: %s', e)
        logger.error('%s', traceback.format_exc())
        return 1
if __name__ == '__main__':
    sys.exit(main())


def run_decision_slice(canonical_bundle: dict) -> dict:
    """Run the first-live decision slice end-to-end."""
    import pandas as pd

    from backend.loans_analytics.multi_agent.feature_store.builder import build_feature_store
    from backend.loans_analytics.multi_agent.orchestrator.decision_orchestrator import DecisionOrchestrator
    from backend.loans_analytics.multi_agent.orchestrator.run_first_live_agents import run_first_live_agents
    from backend.src.data_quality.engine import run_data_quality
    from backend.src.kpi_engine.engine import run_metric_engine
    from backend.src.marts.build_all_marts import build_all_marts

    marts = build_all_marts(canonical_bundle)
    loans = canonical_bundle.get("loans", pd.DataFrame())
    quality = run_data_quality(loans)
    metrics_result = run_metric_engine(marts, quality)
    features = build_feature_store(marts, metrics_result)

    flat_metrics: dict = {}
    for key in ("executive_metrics", "risk_metrics", "pricing_metrics"):
        for mr in metrics_result.get(key, []):
            flat_metrics[mr.metric_id] = mr.value

    agent_outputs = run_first_live_agents(marts, flat_metrics, features, quality)
    orchestrator = DecisionOrchestrator(agent_outputs, flat_metrics)

    return orchestrator.run()
