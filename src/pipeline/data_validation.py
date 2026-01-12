import logging
from typing import Any, Dict

import great_expectations as gx
import polars as pl

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Data Validation layer using Great Expectations.
    Enforces Data Contracts between Bronze and Silver layers.
    """

    def __init__(self):
        # Use an ephemeral context for zero-config validation
        self.context = gx.get_context()

    def validate_bronze(self, df: pl.DataFrame) -> Dict[str, Any]:
        """
        Validate raw data (Bronze layer).
        Ensures basic structural integrity.
        """
        logger.info("Validating Bronze data...")
        pdf = df.to_pandas()

        datasource_name = "bronze_datasource"
        if datasource_name in self.context.datasources:
            self.context.delete_datasource(datasource_name)

        datasource = self.context.sources.add_pandas(name=datasource_name)
        asset_name = "bronze_asset"
        data_asset = datasource.add_dataframe_asset(name=asset_name)

        batch_request = data_asset.build_batch_request(dataframe=pdf)
        validator = self.context.get_validator(
            batch_request=batch_request, expectation_suite_name="bronze_suite"
        )

        # Bronze Expectations: Basic existence and non-nulls
        validator.expect_column_to_exist("loan_id")
        validator.expect_column_to_exist("disbursement_amount")
        validator.expect_column_values_to_not_be_null("loan_id")

        results = validator.validate()
        return results.to_json_dict()

    def validate_silver(self, df: pl.DataFrame) -> Dict[str, Any]:
        """
        Validate conformed data (Silver layer).
        Ensures strict business logic and data type contracts.
        """
        logger.info("Validating Silver data...")
        pdf = df.to_pandas()

        datasource_name = "silver_datasource"
        if datasource_name in self.context.datasources:
            self.context.delete_datasource(datasource_name)

        datasource = self.context.sources.add_pandas(name=datasource_name)
        asset_name = "silver_asset"
        data_asset = datasource.add_dataframe_asset(name=asset_name)

        batch_request = data_asset.build_batch_request(dataframe=pdf)
        validator = self.context.get_validator(
            batch_request=batch_request, expectation_suite_name="silver_suite"
        )

        # Silver Expectations: Business logic thresholds
        validator.expect_column_values_to_not_be_null("customer_id")
        validator.expect_column_values_to_be_between("disbursement_amount", min_value=0)
        validator.expect_column_values_to_be_between(
            "interest_rate_apr", min_value=0, max_value=1.0
        )

        # Schema verification (indirectly via types)
        # Note: In Silver, we already cast to Decimal in Polars,
        # but to_pandas() might convert to float/object.

        results = validator.validate()
        return results.to_json_dict()
