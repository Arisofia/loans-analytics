import great_expectations as gx


def init_gx_project() -> None:
    """Initialize GX file-based context and create the initial suite."""
    context = gx.get_context()

    suite_name = "loan_tape_ingestion"
    suite = gx.ExpectationSuite(name=suite_name)
    suite = context.suites.add(suite)

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
        suite.add_expectation(gx.expectations.ExpectColumnToExist(column=col))

    # 2. Nullity Constraints
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="loan_id"))

    # 3. Numeric Bounds
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="interest_rate_apr",
            min_value=0,
            max_value=1.5,  # 150% APR limit
        )
    )

    suite.save()
    print(f"Great Expectations suite '{suite_name}' initialized successfully.")


if __name__ == "__main__":
    init_gx_project()
