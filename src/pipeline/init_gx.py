import great_expectations as gx
from great_expectations.core.expectation_configuration import ExpectationConfiguration


def init_gx_project() -> None:
    """Initialize GX file-based context and create the initial suite."""
    context = gx.get_context()

    suite_name = "loan_tape_ingestion"
    suite = context.add_or_update_expectation_suite(expectation_suite_name=suite_name)

    # 1. Schema Integrity: Required Columns
    required_columns = [
        "loan_id",
        "customer_id",
        "disbursement_date",
        "disbursement_amount",
        "interest_rate_apr",
        "outstanding_loan_value",
    ]
    for col in required_columns:
        suite.add_expectation(
            ExpectationConfiguration(
                expectation_type="expect_column_to_exist", kwargs={"column": col}
            )
        )

    # 2. Nullity Constraints
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_not_be_null", kwargs={"column": "loan_id"}
        )
    )

    # 3. Numeric Bounds
    suite.add_expectation(
        ExpectationConfiguration(
            expectation_type="expect_column_values_to_be_between",
            kwargs={
                "column": "interest_rate_apr",
                "min_value": 0,
                "max_value": 1.5,  # 150% APR limit
            },
        )
    )

    context.save_expectation_suite(suite)
    print(f"Great Expectations suite '{suite_name}' initialized successfully.")


if __name__ == "__main__":
    init_gx_project()
