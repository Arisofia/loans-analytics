# KPI Mapping Table for Presentation

| KPI Name                        | Department/Agent      | Data Source (JSON/API)                                 | Dashboard/Slide Section           | Notes/Calculation                                 |
|---------------------------------|-----------------------|--------------------------------------------------------|-----------------------------------|---------------------------------------------------|
| Total Customers                 | Growth/Sales          | traction.total_customers                               | Traction, Growth, Sales           | Count of unique customers                         |
| Total Loans                     | Growth/Sales          | traction.total_loans                                   | Traction, Growth, Sales           | Count of loans                                    |
| Total Volume (USD)              | Growth/Sales          | traction.total_volume_usd                              | Traction, Growth, Sales           | Sum of loan volume                                |
| Monthly Active Clients          | Growth/Sales          | traction.monthly_active_clients_latest                  | Traction, Growth, Sales           | Active clients in latest month                    |
| Outstanding Balance (USD)       | Growth/Sales          | traction.outstanding_balance_usd                        | Traction, Growth, Sales           | Current outstanding balance                       |
| Volume/Clients/Balance MoM/QoQ/YoY | Growth/Sales      | traction.growth_metrics                                | Traction, Growth, Sales           | Growth metrics                                    |
| PAR_90                          | Risk                  | delinquency.par90_latest                                | Risk, Portfolio Health             | Portfolio at risk >90 days                        |
| PAR_7                           | Risk                  | delinquency.par7_latest                                 | Risk                              | Portfolio at risk >7 days                         |
| Portfolio at Risk 30 DPD        | Risk                  | delinquency.portfolio_at_risk_30dpd                     | Risk                              | Balance at risk >30 days past due                 |
| Total Balance                   | Risk                  | delinquency.total_balance                               | Risk                              | Total portfolio balance                           |
| PAR_7 MoM/QoQ/YoY               | Risk                  | delinquency.par_metrics                                 | Risk                              | PAR_7 change metrics                              |
| Collection Rate                 | Finance               | collections.collection_rate_latest                      | Collections, Finance               | Latest collection rate                            |
| Payments Received/Scheduled     | Finance               | collections.total_payments_received_latest / collections.total_payments_scheduled_latest | Collections, Finance | Payments metrics                                    |
| Collection Rate MoM/QoQ/YoY     | Finance               | collections.collection_metrics                          | Collections, Finance               | Collection rate change metrics                    |
| CDR Latest                      | Risk/Finance          | curves.cdr_latest                                       | Risk, Finance                      | Cumulative default rate                           |
| Written Off Amount              | Risk/Finance          | curves.written_off_amount                               | Risk, Finance                      | Amount written off                                |
| Starting Balance                | Risk/Finance          | curves.starting_balance                                 | Risk, Finance                      | Starting balance                                  |
| Liquidation Rate                | Risk/Finance          | curves.liquidation_rate                                 | Risk, Finance                      | Liquidation rate                                  |
| Average APR                     | CFO/Finance           | characteristics.average_apr                             | Finance, Portfolio Characteristics | Average annual percentage rate                     |
| Average Loan Size (USD)         | CFO/Finance           | characteristics.average_loan_size_usd                   | Finance, Portfolio Characteristics | Average loan size                                 |
| Interest Rate Distribution      | CFO/Finance           | characteristics.interest_rate_distribution              | Finance, Portfolio Characteristics | Distribution of interest rates                    |
| Cashflow Simulation             | CFO/Finance           | cashflow_simulation.*                                   | Finance, Cashflow                  | Scenario, forecast, multipliers, recovery rate     |
| Total Assets/Liabilities/Equity | CFO/Finance           | financials.balance_sheet                                | Finance, Balance Sheet             | Financial position                                |
| Cash Balance                    | CFO/Finance           | financials.balance_sheet.cash_balance_usd               | Finance, Balance Sheet             | Cash on hand                                      |
| Net Worth                       | CFO/Finance           | financials.balance_sheet.net_worth_usd                  | Finance, Balance Sheet             | Net worth                                         |
| Net Income                      | CFO/Finance           | financials.income_statement.net_income_usd              | Finance, Income Statement          | Net income                                        |
| Runway Months                   | CFO/Finance           | financials.income_statement.runway_months               | Finance, Income Statement          | Months of runway                                  |
| Debt to Equity Ratio            | CFO/Finance           | financials.income_statement.debt_to_equity_ratio        | Finance, Income Statement          | Debt/equity ratio                                 |
| Data Freshness/Completeness     | Compliance            | data_quality.data_freshness_hours / data_completeness_pct | Compliance, Data Quality         | Data quality metrics                               |
| Validation Status               | Compliance            | data_quality.validation_status                          | Compliance, Data Quality           | Data validation status                             |
