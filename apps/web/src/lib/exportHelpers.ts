import type { LoanRow, ProcessedAnalytics } from '@/types/analytics'

type LoanRowWithLtv = LoanRow & { ltv: string }

const loanHeaders: Array<keyof LoanRowWithLtv> = [
  'loan_amount',
  'appraised_value',
  'borrower_income',
  'monthly_debt',
  'loan_status',
  'interest_rate',
  'principal_balance',
  'dpd_status',
  'ltv',
]

function escapeCsvValue(value: string): string {
  // Escape values containing quotes, commas, or any line breaks (CR, LF, or CRLF)
  if (/[",\r\n]/.test(value)) {
    return `"${value.replaceAll('"', '""')}"`
  }
  return value
}

const sanitizeMarkdownCell = (value: string): string =>
  value
    .replace(/[\r\n]+/g, ' ')
    .replace(/\\/g, '\\\\')
    .replace(/[|`]/g, (match) => `\\${match}`)

const formatPercentage = (value: number, digits = 1): string => `${value.toFixed(digits)}%`

export function processedAnalyticsToCSV(analytics: ProcessedAnalytics): string {
  const rows: LoanRowWithLtv[] = analytics.loans.map((loan) => ({
    ...loan,
    ltv: ((loan.loan_amount / Math.max(loan.appraised_value, 1)) * 100).toFixed(1),
  }))
  const headerRow = loanHeaders.join(',')
  if (!rows.length) {
    return headerRow
  }

  const csvRows = rows.map((row) =>
    loanHeaders
      .map((key) => {
        const value = row[key]
        return value === undefined ? '' : escapeCsvValue(String(value))
      })
      .join(',')
  )
  return [headerRow, ...csvRows].join('\n')
}

export function processedAnalyticsToJSON(analytics: ProcessedAnalytics): string {
  return JSON.stringify(
    {
      generatedAt: new Date().toISOString(),
      kpis: analytics.kpis,
      treemap: analytics.treemap,
      rollRates: analytics.rollRates,
      growthProjection: analytics.growthProjection,
      loans: analytics.loans,
    },
    null,
    2,
  )
}

export function processedAnalyticsToMarkdown(analytics: ProcessedAnalytics): string {
  const { kpis, treemap, rollRates, growthProjection } = analytics

  const kpiRows = [
    { label: 'Delinquency rate', value: formatPercentage(kpis.delinquencyRate) },
    { label: 'Portfolio yield', value: formatPercentage(kpis.portfolioYield) },
    { label: 'Average LTV', value: formatPercentage(kpis.averageLTV) },
    { label: 'Average DTI', value: formatPercentage(kpis.averageDTI) },
    { label: 'Loan count', value: kpis.loanCount.toLocaleString() },
  ]
    .map((entry) => `| ${entry.label} | ${entry.value} |`)
    .join('\n')

  const treemapSection =
    treemap.length > 0
      ? treemap
          .map(
            (entry) =>
              `| ${sanitizeMarkdownCell(entry.label)} | ${entry.value.toLocaleString()} | ${sanitizeMarkdownCell(entry.color)} |`,
          )
          .join('\n')
      : '| No treemap data | - | - |'

  const rollRatesSection =
    rollRates.length > 0
      ? rollRates
          .map(
            (entry) =>
              `| ${sanitizeMarkdownCell(entry.from)} → ${sanitizeMarkdownCell(entry.to)} | ${formatPercentage(entry.percent)} |`,
          )
          .join('\n')
      : '| No roll-rate data | - |'

  const growthSection =
    growthProjection.length > 0
      ? growthProjection
          .map(
            (entry) =>
              `| ${sanitizeMarkdownCell(entry.label)} | ${entry.yield.toFixed(1)} | ${entry.loanVolume.toLocaleString()} |`,
          )
          .join('\n')
      : '| No growth projection data | - | - |'

  return [
    '# Analytics Report',
    '',
    '## KPIs',
    '| Metric | Value |',
    '| --- | --- |',
    kpiRows,
    '',
    '## Treemap',
    '| Label | Value | Color |',
    '| --- | --- | --- |',
    treemapSection,
    '',
    '## Roll Rates',
    '| Transition | Percent |',
    '| --- | --- |',
    rollRatesSection,
    '',
    '## Growth Projection',
    '| Month | Yield | Loan Volume |',
    '| --- | --- | --- |',
    growthSection,
  ]
    .filter(Boolean)
    .join('\n')
}
