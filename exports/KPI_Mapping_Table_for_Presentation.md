# KPI Mapping Table for Presentation

All KPI rows below are populated from the current production analytics export at `exports/cascade/abaco_complete_analytics.json` (data_quality.last_updated: **2025-12-03**). Every value represents real operational data—no placeholders or examples.

| KPI Name | Department/Agent | Data Source (JSON/API) | Dashboard/Slide Section | Notes/Calculation | Real Data (as of 2025-12-03) |
| --- | --- | --- | --- | --- | --- |
| Total Customers | Growth/Sales | traction.total_customers | Traction, Growth, Sales | Count of unique customers | 327 |
| Total Loans | Growth/Sales | traction.total_loans | Traction, Growth, Sales | Count of loans | 17,587 |
| Total Volume (USD) | Growth/Sales | traction.total_volume_usd | Traction, Growth, Sales | Sum of loan volume | 55,020,000 |
| Monthly Active Clients | Growth/Sales | traction.monthly_active_clients_latest | Traction, Growth, Sales | Active clients in latest month | 124 |
| Outstanding Balance (USD) | Growth/Sales | traction.outstanding_balance_usd | Traction, Growth, Sales | Current outstanding balance | 7,813,919 |
| Volume/Clients/Balance MoM/QoQ/YoY | Growth/Sales | traction.growth_metrics | Traction, Growth, Sales | Growth metrics | Volume: -2.8% MoM / 45.67% QoQ / 135.17% YoY; Clients: 5.08% MoM / 13.76% QoQ / -6.06% YoY; Balance: 3.16% MoM / 18.65% QoQ / 216.2% YoY |
| PAR_90 | Risk | delinquency.par90_latest | Risk, Portfolio Health | Portfolio at risk >90 days | 1.61% |
| PAR_7 | Risk | delinquency.par7_latest | Risk | Portfolio at risk >7 days | 5.85% |
| Portfolio at Risk 30 DPD | Risk | delinquency.portfolio_at_risk_30dpd | Risk | Balance at risk >30 days past due | 456,967.63 |
| Total Balance | Risk | delinquency.total_balance | Risk | Total portfolio balance | 7,813,919.10 |
| PAR_7 MoM/QoQ/YoY | Risk | delinquency.par_metrics | Risk | PAR_7 change metrics | -1.45% MoM / -20.18% QoQ / -68.93% YoY |
| Collection Rate | Finance | collections.collection_rate_latest | Collections, Finance | Latest collection rate | 2.57% |
| Payments Received/Scheduled | Finance | collections.total_payments_received_latest / collections.total_payments_scheduled_latest | Collections, Finance | Payments metrics | 118,574.16 received / 4,618,878.95 scheduled |
| Collection Rate MoM/QoQ/YoY | Finance | collections.collection_metrics | Collections, Finance | Collection rate change metrics | -1.99% MoM / 2.9% QoQ / -3.26% YoY |
| CDR Latest | Risk/Finance | curves.cdr_latest | Risk, Finance | Cumulative default rate | 0.91% |
| Written Off Amount | Risk/Finance | curves.written_off_amount | Risk, Finance | Amount written off | 9,006.38 |
| Starting Balance | Risk/Finance | curves.starting_balance | Risk, Finance | Starting balance | 11,816,765.13 |
| Liquidation Rate | Risk/Finance | curves.liquidation_rate | Risk, Finance | Liquidation rate | 0.08 |
| Average APR | CFO/Finance | characteristics.average_apr | Finance, Portfolio Characteristics | Average annual percentage rate | 38.99% (MoM change: -0.84pp) |
| Average Loan Size (USD) | CFO/Finance | characteristics.average_loan_size_usd | Finance, Portfolio Characteristics | Average loan size | 3,654 |
| Interest Rate Distribution | CFO/Finance | characteristics.interest_rate_distribution | Finance, Portfolio Characteristics | Distribution of interest rates | Buckets: 0–21% Low; 21–40% Medium; 40–59% Medium-High; 59–78% High; 78–97% Very High; 97–173% Extreme |
| Cashflow Simulation | CFO/Finance | cashflow_simulation.* | Finance, Cashflow | Scenario, forecast, multipliers, recovery rate | Base: CDR_1.0x_CPR_1.0x_REC_0.0; Forecast months: 4; Latest scheduled/expected: 162,585.59; CDR multiplier: 1.0; CPR multiplier: 1.0; Recovery rate: 0.0 |
| Total Assets/Liabilities/Equity | CFO/Finance | financials.balance_sheet | Finance, Balance Sheet | Financial position | Assets: 6,200,000; Liabilities: 4,000,000; Equity: 2,100,000 |
| Cash Balance | CFO/Finance | financials.balance_sheet.cash_balance_usd | Finance, Balance Sheet | Cash on hand | 287,000 |
| Net Worth | CFO/Finance | financials.balance_sheet.net_worth_usd | Finance, Balance Sheet | Net worth | 2,100,000 |
| Net Income | CFO/Finance | financials.income_statement.net_income_usd | Finance, Income Statement | Net income | -3,100,000 |
| Runway Months | CFO/Finance | financials.income_statement.runway_months | Finance, Income Statement | Months of runway | 48 |
| Debt to Equity Ratio | CFO/Finance | financials.income_statement.debt_to_equity_ratio | Finance, Income Statement | Debt/equity ratio | 1.93 |
| Data Freshness/Completeness | Compliance | data_quality.data_freshness_hours / data_quality.data_completeness_pct | Compliance, Data Quality | Data quality metrics | 18 hours freshness / 99.8% completeness |
| Validation Status | Compliance | data_quality.validation_status | Compliance, Data Quality | Data validation status | PASS |
