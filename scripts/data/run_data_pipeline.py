import argparse
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from backend.python.logging_config import get_logger, init_sentry
from backend.src.pipeline.orchestrator import UnifiedPipeline
init_sentry(service_name='data_pipeline')
logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Unified Data Pipeline - 4-Phase Execution', formatter_class=argparse.RawDescriptionHelpFormatter, epilog='\nExamples:\n  # Run full pipeline with default config\n  python scripts/data/run_data_pipeline.py\n\n  # Run with specific input file\n  python scripts/data/run_data_pipeline.py --input data/raw/loans.csv\n\n  # Validate configuration and data only\n  python scripts/data/run_data_pipeline.py --mode validate\n\n  # Dry run (ingestion only)\n  python scripts/data/run_data_pipeline.py --mode dry-run\n\n  # Use custom config file\n  python scripts/data/run_data_pipeline.py --config config/custom_pipeline.yml\n        ')
    parser.add_argument('--input', type=Path, help='Path to input CSV file (optional, can use API ingestion)')
    parser.add_argument('--config', type=Path, default=Path('config/pipeline.yml'), help='Path to pipeline configuration file (default: config/pipeline.yml)')
    parser.add_argument('--mode', choices=['full', 'validate', 'dry-run'], default='full', help='Execution mode: full (all phases), validate (stop after transformation), dry-run (ingestion only)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def main():
    args = parse_args()
    logger.info('%s', '=' * 80)
    logger.info('UNIFIED PIPELINE EXECUTION STARTED')
    logger.info('%s', '=' * 80)
    logger.info('Config: %s', args.config)
    logger.info('Input: %s', args.input or 'API ingestion')
    logger.info('Mode: %s', args.mode)
    logger.info('%s', '=' * 80)
    try:
        pipeline = UnifiedPipeline(config_path=args.config if args.config.exists() else None)
        results = pipeline.execute(input_path=args.input, mode=args.mode)
        print('\n' + '=' * 80)
        print('PIPELINE EXECUTION SUMMARY')
        print('=' * 80)
        print(f"Status: {results['status'].upper()}")
        print(f"Run ID: {results['run_id']}")
        print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        print('\nPhase Results:')
        for phase_name, phase_results in results.get('phases', {}).items():
            status_symbol = '[SUCCESS]' if phase_results.get('status') == 'success' else '[FAILED]'
            print(f"  {status_symbol} {phase_name.title()}: {phase_results.get('status', 'unknown')}")
        print('=' * 80)
        if results['status'] == 'success':
            print('\n[SUCCESS] Pipeline execution completed successfully!')
            sys.exit(0)
        else:
            print(f"\n[FAILED] Pipeline execution failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)
    except FileNotFoundError as e:
        logger.error('Configuration file not found: %s', e)
        print('\n[FAILED] Error: Configuration file not found')
        print(f'Please create {args.config} with pipeline settings')
        print('\nSee UNIFIED_WORKFLOW.md for configuration details')
        sys.exit(1)
    except Exception as e:
        logger.error('Pipeline execution failed: %s', e, exc_info=True)
        print(f'\n[FAILED] Pipeline execution failed: {e}')
        sys.exit(1)
if __name__ == '__main__':
    main()
