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
    2
  )
}

export function processedAnalyticsToMarkdown(analytics: ProcessedAnalytics): string {
  const generatedAt = new Date().toISOString()

  const kpiRows = [
    ['Delinquency rate', `${analytics.kpis.delinquencyRate}%`],
    ['Portfolio yield', `${analytics.kpis.portfolioYield}%`],
    ['Average LTV', `${analytics.kpis.averageLTV}%`],
    ['Average DTI', `${analytics.kpis.averageDTI}%`],
    ['Active loans', analytics.kpis.loanCount.toString()],
  ]

  const treemapTable = analytics.treemap.length
    ? [
        '| Segment | Balance | Color |',
        '| --- | ---: | --- |',
        ...analytics.treemap.map(
          (entry) => `| ${entry.label} | ${entry.value.toLocaleString()} | ${entry.color} |`
        ),
      ].join('\n')
    : '_No treemap segments loaded_'

  const rollRateTable = analytics.rollRates.length
    ? [
        '| From (DPD) | To (Status) | Share (%) |',
        '| --- | --- | ---: |',
        ...analytics.rollRates.map(
          (row) => `| ${row.from} | ${row.to} | ${row.percent.toFixed(1)} |`
        ),
      ].join('\n')
    : '_No roll-rate entries loaded_'

  const growthTable = analytics.growthProjection.length
    ? [
        '| Month | Yield | Loan volume |',
        '| --- | ---: | ---: |',
        ...analytics.growthProjection.map(
          (point) => `| ${point.label} | ${point.yield}% | ${point.loanVolume.toLocaleString()} |`
        ),
      ].join('\n')
    : '_No growth projection available_'

  return [
    '# ABACO portfolio analytics export',
    `Generated at: ${generatedAt}`,
    '',
    '## KPI summary',
    '| KPI | Value |',
    '| --- | ---: |',
    ...kpiRows.map((row) => `| ${row[0]} | ${row[1]} |`),
    '',
    '## Treemap breakdown',
    treemapTable,
    '',
    '## Roll-rate cascade',
    rollRateTable,
    '',
    '## Growth projection',
    growthTable,
  ].join('\n')
}

export function processedAnalyticsToMarkdown(analytics: ProcessedAnalytics): string {
  const { kpis, treemap, rollRates, growthProjection } = analytics

  const formatPercent = (value: number): string =>
    Number.isFinite(value) ? `${value.toFixed(1)}%` : '–'

  const sanitizeMarkdownCell = (value: string): string =>
    value
      .replace(/[\r\n]+/g, ' ')
      .replace(/[|`]/g, (match) => `\\${match}`)

  const treemapSection = treemap
    .map((entry) => `| ${sanitizeMarkdownCell(entry.label)} | ${entry.value.toLocaleString()} | ${sanitizeMarkdownCell(entry.color)} |`)
    .join('\n')

  const rollRateSection = rollRates
    .map((rate) => `| ${sanitizeMarkdownCell(rate.from)} | ${sanitizeMarkdownCell(rate.to)} | ${formatPercent(rate.percent)} |`)
    .join('\n')

  const growthSection = growthProjection
    .map((point) => `| ${sanitizeMarkdownCell(point.label)} | ${Number.isFinite(point.yield) ? point.yield.toFixed(1) : '–'} | ${point.loanVolume.toLocaleString()} |`)
    .join('\n')

  const treemapTable = treemapSection || '| – | – | – |'
  const rollRateTable = rollRateSection || '| – | – | – |'
  const growthTable = growthSection || '| – | – | – |'

  return `# Portfolio Analytics Report\n\n` +
    `## KPIs\n` +
    `- Delinquency rate: ${formatPercent(kpis.delinquencyRate)}\n` +
    `- Portfolio yield: ${formatPercent(kpis.portfolioYield)}\n` +
    `- Average LTV: ${formatPercent(kpis.averageLTV)}\n` +
    `- Average DTI: ${formatPercent(kpis.averageDTI)}\n` +
    `- Active loans: ${kpis.loanCount}\n\n` +
    `## Segment Treemap\n` +
    `| Segment | Principal Balance | Color |\n` +
    `|---|---|---|\n` +
    `${treemapTable}\n\n` +
    `## Roll-rate Cascade\n` +
    `| From | To | Percent |\n` +
    `|---|---|---|\n` +
    `${rollRateTable}\n\n` +
    `## Growth Path\n` +
    `| Month | Yield | Loan Volume |\n` +
    `|---|---|---|\n` +
    `${growthTable}`
}
