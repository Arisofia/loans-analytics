from pathlib import Path
from typing import Any, Dict, Union

from prefect import flow, get_run_logger, task

from src.agents.tools import send_slack_notification
from src.pipeline.data_ingestion import IngestionResult, UnifiedIngestion
from src.pipeline.data_transformation import (TransformationResult,
                                              UnifiedTransformation)
from src.pipeline.data_validation_gx import validate_loan_data
from src.pipeline.kpi_calculation import (CalculationResultV2,
                                          UnifiedCalculationV2)
from src.pipeline.orchestrator import PipelineConfig
from src.pipeline.output import OutputResult, UnifiedOutput


@task(retries=3, retry_delay_seconds=60)
def ingestion_task(config: Dict[str, Any], input_file: Path) -> IngestionResult:
    logger = get_run_logger()
    logger.info("Starting ingestion for %s", input_file)
    ingestion = UnifiedIngestion(config)
    # Assume file source for now
    raw_archive_dir = Path(config.get("run", {}).get("raw_archive_dir", "data/archives/cascade"))
    result = ingestion.ingest_file(input_file, archive_dir=raw_archive_dir)

    # Integrate Great Expectations
    dq_passed = validate_loan_data(result.df)
    if not dq_passed:
        logger.warning("Great Expectations validation failed!")
        send_slack_notification(
            f"⚠️ *Data Quality Alert*: GX validation failed for {input_file}",
            channel="kpi-compliance",
        )

    # Map to typed container if needed (UnifiedIngestion returns a dataclass-like object)
    if isinstance(result, IngestionResult):
        return result
    # If result is a legacy object, wrap into IngestionResult
    return IngestionResult(df=result.df, run_id=getattr(result, "run_id", "unknown"), metadata={})


@task
def transformation_task(
    config: Dict[str, Any], df: Union[TransformationResult, Any], run_id: str
) -> TransformationResult:
    logger = get_run_logger()
    logger.info("Starting transformation for run %s", run_id)
    transformation = UnifiedTransformation(config, run_id=run_id)
    return transformation.transform(df, user="prefect")


@task
def calculation_task(
    config: Dict[str, Any], df: Union[TransformationResult, Any], run_id: str
) -> CalculationResultV2:
    logger = get_run_logger()
    logger.info("Starting KPI calculation for run %s", run_id)
    calculation = UnifiedCalculationV2(config, run_id=run_id)
    # For now, no baseline metrics passed to simplify
    return calculation.calculate(df, baseline_metrics=None)


@task
def output_task(
    config: Dict[str, Any],
    transformation_result: TransformationResult,
    calculation_result: CalculationResultV2,
    run_id: str,
) -> OutputResult:
    logger = get_run_logger()
    logger.info("Starting output persistence for run %s", run_id)
    output = UnifiedOutput(config, run_id=run_id)

    # We can add Supabase persistence here or in UnifiedOutput.persist
    result = output.persist(
        transformation_result.df,
        calculation_result.metrics,
        metadata={
            "transformation": transformation_result.lineage,
            "calculation": calculation_result.audit_trail,
        },
        run_ids={"pipeline": run_id},
    )
    return result


@flow(name="Abaco Data Pipeline")
def abaco_pipeline_flow(
    input_file: str = "data/archives/abaco_portfolio_calculations.csv",
) -> OutputResult:
    config_mgr = PipelineConfig()
    config = config_mgr.config
    input_path = Path(input_file)

    ingest_res = ingestion_task(config, input_path)
    # Prefect tasks return proxies; extract run_id and dataframe via attributes
    run_id = f"prefect_{ingest_res.run_id}"

    trans_res = transformation_task(config, ingest_res.df, run_id)
    calc_res = calculation_task(config, trans_res.df, run_id)
    out_res = output_task(config, trans_res, calc_res, run_id)

    return out_res


if __name__ == "__main__":
    abaco_pipeline_flow()
