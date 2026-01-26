import polars as pl

# Precision 38, Scale 4 is suitable for high-precision financial calculations
# and aligns with the mandate for Decimal types in the transformation report.

INVOICE_SCHEMA = {
    "loan_id": pl.Utf8,
    "customer_id": pl.Utf8,
    "disbursement_date": pl.Date,
    "disbursement_amount": pl.Decimal(precision=38, scale=4),
    "interest_rate_apr": pl.Decimal(precision=38, scale=4),
    "origination_fee": pl.Decimal(precision=38, scale=4),
    "origination_fee_taxes": pl.Decimal(precision=38, scale=4),
    "loan_end_date": pl.Date,
    "days_past_due": pl.Int64,
}

PAYMENT_SCHEMA = {
    "loan_id": pl.Utf8,
    "true_payment_date": pl.Date,
    "true_total_payment": pl.Decimal(precision=38, scale=4),
    "true_principal_payment": pl.Decimal(precision=38, scale=4),
    "true_interest_payment": pl.Decimal(precision=38, scale=4),
    "true_fee_payment": pl.Decimal(precision=38, scale=4),
    "true_other_payment": pl.Decimal(precision=38, scale=4),
    "true_tax_payment": pl.Decimal(precision=38, scale=4),
    "true_fee_tax_payment": pl.Decimal(precision=38, scale=4),
    "true_rebates": pl.Decimal(precision=38, scale=4),
}

CLIENT_SCHEMA = {
    "customer_id": pl.Utf8,
    "customer_name": pl.Utf8,
    "sector_segment": pl.Utf8,
    "business_segment": pl.Utf8,
    "industry_segment": pl.Utf8,
    "kam_id": pl.Utf8,
}
