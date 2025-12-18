# KPI Catalog
Each KPI includes owner, agent, source, thresholds, drill-down, runbook, and alert channel.
# KPI Catalog
Each KPI includes owner, agent, source, thresholds, drill-down, runbook, and alert channel.

| KPI                 | Definition                                        | Owner            | Agent         | Source                   | Thresholds                          | Drill-down                                    | Runbook                         | Alert channel               |
| ------------------- | ------------------------------------------------- | ---------------- | ------------- | ------------------------ | ----------------------------------- | --------------------------------------------- | ------------------------------- | --------------------------- |
| NPL% / PAR30/60/90  | Outstanding balance 30/60/90+ days past due       | Risk Ops         | RiskAnalyst   | Loans fact + aging view  | Amber >3%, Red >5%                  | Delinquent accounts table with cohort filters | `runbooks/kpi-breach.md`        | Slack `#risk-alerts`, email |
| LGD / ECL           | Loss given default and expected credit loss       | Risk Modeling    | RiskAnalyst   | Models + write-off table | Red if variance >10% vs plan        | Model version comparison, segment loss curves | `runbooks/kpi-breach.md`        | Slack `#risk-alerts`, email |
| Approval Rate       | Approved apps / total apps                        | Credit Policy    | PlatformAgent | Applications fact        | Amber <40%, Red <35%                | Funnel by channel/segment                     | `runbooks/ingestion-failure.md` | Slack `#ops-alerts`         |
| Auto-decision Rate  | % auto-approved/-declined                         | Credit Ops       | PlatformAgent | Decision engine logs     | Amber <70%                          | Rule hit table, manual override queue         | `runbooks/kpi-breach.md`        | Slack `#ops-alerts`         |
| TAT (Decision)      | Median time to decision                           | Credit Ops       | PlatformAgent | Decision logs            | Red > 60s                           | Latency by step                               | `runbooks/ingestion-failure.md` | Slack `#ops-alerts`         |
| Roll Rate Matrix    | Transitions between delinquency buckets           | Collections      | Sentinel      | Payments + aging         | Red if roll-forward +5% vs baseline | Heatmap → loan list per cell                  | `runbooks/kpi-breach.md`        | Slack `#collections`, email |
| Cure Rate           | % delinquent loans cured per period               | Collections      | Sentinel      | Payments                 | Red < target by 3pp                 | Segment table (agent, bucket, cohort)         | `runbooks/kpi-breach.md`        | Slack `#collections`, email |
| Promise-to-Pay Kept | Kept PTPT / total PTPT                            | Collections      | Sentinel      | Promise logs             | Red <80%                            | Agent and borrower drill-down                 | `runbooks/kpi-breach.md`        | Slack `#collections`, email |
| CAC / LTV           | Acquisition cost vs lifetime value                | Growth           | GrowthCoach   | Marketing + repayment    | Red if CAC/LTV >0.3                 | Channel table, cohort profitability           | `runbooks/kpi-breach.md`        | Slack `#growth`             |
| Data Quality        | Freshness, completeness, duplicates, schema drift | Data Engineering | Integrator    | Pipelines + monitors     | Red if freshness >1h or null %>1%   | Failed checks, offending rows                 | `runbooks/schema-drift.md`      | Slack `#data`, email        |

# KPI Mapping Table

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
| Payments Received/Scheduled     | Finance               | collections.total_payments_received_latest / total_payments_scheduled_latest | Collections, Finance | Payments metrics                                    |
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
## Actionability rules

- Every chart links to a drill-down table and its runbook. Next-best action is documented per KPI (collections playbook, credit tweak, data fix).
- Owners approve KPI definition changes via PRs; PR template requires “KPI impact” and “data sources touched”.
- Alerts route to the owner’s channel with SLA and runbook link; MTTR/MTTD tracked in postmortems.
## Continuous learning

- For KPI breaches or model drift: open postmortem, capture cause/fix/prevention, add tests/alerts, and record MTTR/MTTD. Link postmortem to relevant runbook.
