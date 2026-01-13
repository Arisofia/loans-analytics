#!/usr/bin/env python3
"""
Example application entry point with tracing enabled.

This script demonstrates how to initialize tracing at application startup
and use it throughout your application.
"""

import logging
import sys

# Initialize tracing FIRST before importing any other application modules
from python.tracing_setup import configure_tracing, is_tracing_enabled

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point with tracing."""
    # Configure tracing at startup
    logger.info("Initializing application with tracing...")
    configure_tracing()

    if is_tracing_enabled():
        logger.info("✓ Tracing enabled - telemetry will be sent to Azure Application Insights")
    else:
        logger.warning("⚠ Tracing disabled - no telemetry will be collected")
        logger.warning("  Set APPLICATIONINSIGHTS_CONNECTION_STRING to enable tracing")

    # Now import and use your application modules
    # They will automatically benefit from tracing
    from python.agents.orchestrator import AgentOrchestrator
    from python.pipeline.orchestrator import PipelineOrchestrator

    # Example: Run agent
    logger.info("Running agent orchestrator...")
    orchestrator = AgentOrchestrator()
    result = orchestrator.run(
        input_data={"query": "What is the current portfolio risk?"},
        agent_config={
            "name": "RiskAnalyzer",
            "role": "Risk Assessment Analyst",
            "goal": "Analyze portfolio risk metrics",
        },
    )
    logger.info(f"Agent result: {result['output'][:100]}...")

    # Example: Run pipeline (if you have input data)
    # logger.info("Running pipeline...")
    # pipeline = PipelineOrchestrator()
    # pipeline_result = pipeline.execute(
    #     input_file=Path("data/input.csv"),
    #     user="example_user",
    #     action="automated"
    # )
    # logger.info(f"Pipeline status: {pipeline_result['status']}")

    logger.info("✓ Application completed successfully")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application failed: {e}", exc_info=True)
        sys.exit(1)
