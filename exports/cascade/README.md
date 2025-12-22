# Cascade Debt Analytics Integration

## Overview

This directory contains Abaco Capital's analytics data exported from Cascade Debt platform. These exports are integrated into our repository to maintain historical records, enable dashboard development, and support automated reporting.

## Files

### `abaco_risk_overview.json`

Comprehensive JSON export of all risk metrics and analytics views from Cascade Debt.

**Contains:**

- Risk Overview snapshot (Traction, Delinquency, Characteristics, Collection)
- Key Indicators (Cumulative & Current Traction, Portfolio Performance)
- Configuration for all 11 available Cascade views
- API integration notes for automation

**Data Freshness:**

- Loan Tape As Of: 2025-12-02
- Last Updated: 2025-12-03
- Date Range: 2023-01-03 to 2025-12-31

## Key Metrics Snapshot

### Portfolio Traction

```
Total Unique Customers: 327
Total Loans: 17,587
Total Volume: $55.02M USD
Avg Monthly Volume (12m): $2.79M USD
Outstanding Portfolio: $7.76M USD
Active Loans: 1,191
Active Borrowers: 123
```

### Delinquency (Performance)

```
PAR 30: 3.31%
PAR 90 (Latest): 1.61%
RDR 90 @ 12 Months: 0.98%
Bad 90 @ 6 Months: 1.01%
Bad 90 @ 12 Months: 0.58%
```

### Characteristics

```
Average APR (12m): 38.99%
Average Loan Size (12m): $3,654 USD
Average Term (12m): 54 days
Average Headline Interest Rate (12m): 3,712.33%
```

### Collection

```
Collection Rate (Latest): 2.57%
Month-over-Month Change: -104.07% (-97.59%)
```

## Available Views in Cascade

All of these views are accessible via Cascade API:

1. **Risk Overview** - High-level risk metrics summary
2. **Key Indicators** - Detailed performance indicators
3. **Traction** - Volume and customer acquisition metrics
4. **Delinquency** - Delinquency rate analysis (PAR, RDR)
5. **Collection** - Collection rates and recovery metrics
6. **Curves** - Vintage performance curves
7. **Cohort** - Cohort analysis by origination period
8. **Characteristics** - Loan and borrower characteristics
9. **Cashflow Simulation** - Projected cash flows and scenarios
10. **Financials - Key Indicators** - Financial performance metrics
11. **Financials - Statements** - Detailed financial statements

## Integration with Repository

### Automated Updates

These files should be updated daily via GitHub Actions workflow:

```yaml
name: Update Cascade Data
on:
  schedule:
    - cron: '0 2 * * *' # Daily at 2 AM UTC
jobs:
  update-cascade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Fetch latest from Cascade
        run: |
          # Call Cascade API with OAuth 2.0 or API Key
          # Parse JSON and update exports/cascade/abaco_risk_overview.json
      - name: Commit changes
        run: |
          git add exports/cascade/
          git commit -m "chore(cascade): update analytics data"
          git push
```

### API Credentials

Store Cascade API credentials in GitHub Secrets:

- `CASCADE_API_KEY` - Cascade Debt API key
- `CASCADE_PARTNER_ID` - Should be "abaco"

### Error Handling

When updating:

1. Validate JSON structure before commit
2. Check for data consistency (no null values in critical fields)
3. Log all API errors to GitHub Actions logs
4. Retry failed requests with exponential backoff
5. Notify team if update fails 3 consecutive times

## Dashboard Integration

### React Components

To use this data in React dashboards:

```typescript
import cascadeData from '../exports/cascade/abaco_risk_overview.json';

function RiskDashboard() {
  const { overview, key_indicators } = cascadeData;

  return (
    <div>
      <h2>Portfolio Traction</h2>
      <KPICard
        title="Total Customers"
        value={overview.traction.total_unique_clients}
      />
      <KPICard
        title="Total Volume"
        value={`$${overview.traction.total_volume_usd / 1e6}M`}
      />
    </div>
  );
}
```

## Data Quality Checks

Before merging PR with updated Cascade data:

- [ ] All numeric fields are positive (no negative portfolio values)
- [ ] Percentages are between 0 and 100
- [ ] Date fields are valid ISO 8601 format
- [ ] No null or undefined values in critical metrics
- [ ] Data is newer than previous export
- [ ] Customer/loan counts are monotonically increasing

## Troubleshooting

### Data Not Updating

1. Check GitHub Actions workflow logs for API errors
2. Verify CASCADE_API_KEY and CASCADE_PARTNER_ID are set
3. Test API connection: `curl https://api.cascadedebt.com/health`
4. Check Cascade Debt status page for any outages

### Stale Data Warning

If no update for > 24 hours, PR comment will be added with warning.

## References

- [Cascade Debt Documentation](https://docs.cascadedebt.com)
- [Cascade API Endpoints](https://api.cascadedebt.com/docs)
- [GitHub Actions Workflows](.../../.github/workflows)
