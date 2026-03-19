# Loan Tape Import Report (2026-03-19)

Generated at: 2026-03-19T02:45:56.355518+00:00

## Raw Dataset Profile
| Dataset | Rows | Columns |
|---|---:|---:|
| loan_data | 18101 | 28 |
| payment_schedule | 18101 | 16 |
| real_payment | 19348 | 18 |
| customer_data | 18101 | 38 |
| collateral | 18101 | 12 |

## Canonical Output Profile (LoanTapeLoader)
| Table | Rows | Columns |
|---|---:|---:|
| dim_loan | 18101 | 29 |
| fact_schedule | 18101 | 16 |
| fact_real_payment | 19348 | 18 |
| dim_customer | 18101 | 38 |
| dim_collateral | 18101 | 12 |

## Loan ID Cross-Validation
- loan_ids in dim_loan: 15110
- loan_ids in fact_schedule: 15110
- loan_ids in fact_real_payment: 14378
- loan_ids in dim_collateral: 15110
- schedule not in dim_loan: 0
- real_payment not in dim_loan: 0
- collateral not in dim_loan: 0
- dim_loan not in schedule: 0
- dim_loan not in real_payment: 732

## Mapping - loan_data.csv
| Raw Column | Canonical Column |
|---|---|
| Customer ID | client_id |
| Loan ID | loan_id |
| Product Type | product_type |
| Disbursement Date | disbursement_date |
| Disbursement Amount | original_principal |
| Loan Currency | currency |
| Interest Rate APR | interest_rate |
| Term | term_months |
| Outstanding Loan Value | outstanding_loan_value |

## Mapping - payment_schedule.csv
| Raw Column | Canonical Column |
|---|---|
| Loan ID | loan_id |
| Payment Date | scheduled_date |
| Total Payment | scheduled_total |
| Principal Payment | scheduled_principal |
| Interest Payment | scheduled_interest |
| Fee Payment | scheduled_fee |
| Other Payment | scheduled_other |

## Mapping - real_payment.csv
| Raw Column | Canonical Column |
|---|---|
| Loan ID | loan_id |
| True Payment Date | payment_date |
| True Total Payment | paid_total |
| True Principal Payment | paid_principal |
| True Interest Payment | paid_interest |
| True Fee Payment | paid_fee |
| True Other Payment | paid_other |

## Mapping - customer_data.csv
| Raw Column | Canonical Column |
|---|---|
| Customer ID | client_id |
| Cliente | client_name |
| Sales Agent | kam |
| Industry | industry |

## Mapping - collateral.csv
| Raw Column | Canonical Column |
|---|---|
| Loan ID | loan_id |
| Collateral Type | collateral_type |
| Collateral Current | collateral_value |

