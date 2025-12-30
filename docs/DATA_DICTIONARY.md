# Abaco Analytics - Data Dictionary

## data/abaco/loan_data.csv
- loan_id: Unique loan identifier
- customer_id: Foreign key to customer_data
- disbursement_date: Date loan was disbursed
- disbursement_amount: Principal amount disbursed
- interest_rate_apr: Annual percentage rate
- origination_fee: Upfront fee amount
- origination_fee_taxes: Taxes applied to origination fee
- approved_line_amount: Credit line approved
- loan_status: Current status of the loan
- days_in_default: Days in default, if applicable
- ...

## data/abaco/customer_data.csv
- customer_id: Unique customer identifier
- segment: Customer segment (Nimal/Gob/OC/Top)
- subcategoria_linea: Ticket/line band (<10K, 10K-25K, 25K-50K, 50K-100K, >100K)
- kam_id: Key Account Manager ID
- first_disbursement_date: First ever disbursement for this customer
- legal_type: Legal entity type (company/individual/government)
- industry_code: Industry classification code (CIIU/NAICS/etc.)
- ...

## data/abaco/real_payment.csv
- loan_id: Foreign key to loan_data
- true_payment_date: Actual payment date
- true_principal_payment: Principal paid
- true_interest_payment: Interest paid
- true_fee_payment: Fees paid
- true_other_payment: Other charges/fees
- true_tax_payment: Taxes collected
- true_fee_tax_payment: Taxes on fees
- true_rabates: Rebates or refunds
- ...

## data/abaco/payment_schedule.csv
- loan_id: Foreign key to loan_data
- payment_date: Scheduled payment date
- total_payment: Total scheduled payment (principal + interest + fees)
- scheduled_principal: Principal scheduled
- scheduled_interest: Interest scheduled
- ...

## data/abaco/collateral.csv
- loan_id: Foreign key to loan_data
- collateral_type: Type of collateral
- collateral_value: Reported value of collateral
- lien_rank: Lien position / seniority
- ...

## data/support/marketing_spend.csv
- month: Month-end date
- channel: Marketing channel (Digital/Direct/Referral/etc.)
- segment: Customer segment (Nimal/Gob/OC/Top)
- spend: Total spend in that month/channel/segment
- kam_id: KAM associated to that spend (if applicable)

## data/support/payor_map.csv
- customer_id: Customer identifier
- payor_id: Unique payor identifier
- payor_name: Payor name
- effective_date: Date the mapping becomes effective

## data/support/headcount.csv
- month: Month-end date
- function: Function name (Sales/Risk/Collections/...)
- fte_count: Full-time equivalent count
- team: Team name/cluster (Commercial/Credit/Operations)

## data/support/risk_parameters.csv
- segment: Segment (Nimal/Gob/OC/Top/etc.)
- subcategoria_linea: Ticket/line band
- pd: Probability of default
- lgd: Loss given default
- ead_factor: Exposure at default factor

## data/support/targets.csv
- year_month: Month-end date
- customer_type: New / Recurrent / Reactivated
- segment: Segment (Nimal/Gob/OC/Top)
- target_disbursement: Monthly disbursement target
- target_customers: Monthly target for unique customers
