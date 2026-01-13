"""Great Expectations validation helpers for pipeline checks."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import great_expectations as gx
    from great_expectations.data_context import EphemeralDataContext

    HAS_GE = True
except Exception:  # pragma: no cover - optional dependency
    gx = None  # type: ignore
    EphemeralDataContext = None  # type: ignore
    HAS_GE = False


def get_or_create_datasource(
    context: "EphemeralDataContext",
    datasource_name: str,
) -> Any:
    """Get or create a pandas datasource for the given context."""
    try:
        return context.get_datasource(datasource_name)
    except Exception:
        logger.info("Datasource '%s' not found; creating it.", datasource_name)
        return context.sources.add_pandas(name=datasource_name)  # type: ignore


def create_validator_for_dataframe(
    context: "EphemeralDataContext",
    df: pd.DataFrame,
    datasource_name: str,
    asset_name: str,
) -> Any:
    """Create a Great Expectations validator for a Pandas DataFrame."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a Pandas DataFrame.")

    datasource = get_or_create_datasource(context, datasource_name)
    pandas_asset = datasource.add_dataframe_asset(name=asset_name, dataframe=df)
    batch_request = pandas_asset.build_batch_request()

    return context.get_validator(
        batch_request=batch_request,
        create_expectation_suite_with_name=f"{asset_name}_suite",
    )


def validate_data(
    df: pd.DataFrame,
    expectations: List[Dict[str, Any]],
    datasource_name: str,
    asset_name: str,
) -> Dict[str, Any]:
    """Validate a DataFrame against a list of Great Expectations configs."""
    if not HAS_GE:
        logger.warning("Great Expectations not installed; skipping validation.")
        return {"success": True, "skipped": True}

    try:
        context = gx.get_context(project_root_dir=None, mode="ephemeral")
    except Exception as exc:
        logger.error("Failed to initialize Great Expectations context: %s", exc)
        return {"success": False, "error": str(exc)}

    validator = create_validator_for_dataframe(context, df, datasource_name, asset_name)

    for expectation in expectations:
        expectation_type = expectation.get("type")
        if not expectation_type:
            continue
        kwargs = {key: value for key, value in expectation.items() if key != "type"}
        try:
            getattr(validator, expectation_type)(**kwargs)
        except Exception as exc:
            logger.error("Failed to apply expectation %s: %s", expectation_type, exc)

    try:
        result = validator.validate()
    except Exception as exc:
        logger.error("Validation execution failed: %s", exc)
        return {"success": False, "error": str(exc)}

    success = bool(getattr(result, "success", False))
    if not success:
        logger.warning("Great Expectations validation failed.")
    return {"success": success, "details": result}


def _default_expectations() -> List[Dict[str, Any]]:
    return [
        {
            "type": "expect_table_row_count_to_be_between",
            "min_value": 1,
        }
    ]


def validate_loan_data(df: pd.DataFrame) -> bool:
    """Validate loan data with a minimal expectation suite."""
    result = validate_data(
        df,
        _default_expectations(),
        datasource_name="loan_data",
        asset_name="loan_data",
    )
    return bool(result.get("success"))
