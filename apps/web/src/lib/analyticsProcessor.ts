import {
  LoanRow,
  ProcessedAnalytics,
  RollRateEntry,
  TreemapEntry,
  GrowthPoint,
} from '@/types/analytics'

const currencyRegex = /[^\d.-]/g

function toNumber(value: string | number): number {
  if (typeof value === 'number') {
    return value
  }
  const cleaned = value.replace(currencyRegex, '')
  return Number(cleaned) || 0
}

export function parseLoanCsv(content: string): LoanRow[] {
  const rows = content
    .trim()
    .split(/\r?\n/)
    .map((line) => line.split(','))
    .filter((parts) => parts.length >= 7)

  const header = rows.shift()
  if (!header) return []

  const keys = header.map((col) => col.trim().toLowerCase())
  return rows.map((parts) => {
    const record: Record<string, string> = {}
    parts.forEach((value, index) => {
      record[keys[index] ?? `col_${index}`] = value.trim()
    })
    return {
      loan_amount: toNumber(record.loan_amount ?? ''),
      appraised_value: toNumber(record.appraised_value ?? ''),
      borrower_income: toNumber(record.borrower_income ?? ''),
      monthly_debt: toNumber(record.monthly_debt ?? ''),
      loan_status: record.loan_status || 'unknown',
      interest_rate: toNumber(record.interest_rate ?? ''),
      principal_balance: toNumber(record.principal_balance ?? ''),
      dpd_status: record.dpd_status || '',
    }
  })
}

export function processLoanRows(rows: LoanRow[]): ProcessedAnalytics {
  const kpis = computeKPIs(rows)
  const treemap = buildTreemap(rows)
  const rollRates = buildRollRates(rows)
  const growthProjection = buildGrowthProjection(kpis.portfolioYield, kpis.loanCount)

  return {
    kpis,
    treemap,
    rollRates,
    growthProjection,
    loans: rows,
  }
}

function computeKPIs(rows: LoanRow[]) {
  const totalLoans = rows.length
  const delinquentStatuses = ['30-59 days past due', '60-89 days past due', '90+ days past due']
  const delinquentCount = rows.filter((row) => delinquentStatuses.includes(row.loan_status)).length
  const riskRate = totalLoans ? (delinquentCount / totalLoans) * 100 : 0

  const totalPrincipal = rows.reduce((sum, row) => sum + row.principal_balance, 0)
  const weightedInterest = rows.reduce(
    (sum, row) => sum + row.interest_rate * row.principal_balance,
    0
  )
  const portfolioYield = totalPrincipal ? (weightedInterest / totalPrincipal) * 100 : 0

  const averageLTV = rows.reduce(
    (sum, row) => sum + row.loan_amount / Math.max(row.appraised_value, 1),
    0
  )
  const averageDTI = rows.reduce((sum, row) => {
    const income = row.borrower_income / 12
    if (income <= 0) return sum
    return sum + row.monthly_debt / income
  }, 0)

  return {
    delinquencyRate: Number(riskRate.toFixed(2)),
    portfolioYield: Number(portfolioYield.toFixed(2)),
    averageLTV: Number(((averageLTV / Math.max(totalLoans, 1)) * 100).toFixed(1)),
    averageDTI: Number(((averageDTI / Math.max(totalLoans, 1)) * 100).toFixed(1)),
    loanCount: totalLoans,
  }
}

function buildTreemap(rows: LoanRow[]): TreemapEntry[] {
  const map: Record<string, number> = {}
  rows.forEach((row) => {
    map[row.loan_status] = (map[row.loan_status] || 0) + row.principal_balance
  })
  const colors = ['#C1A6FF', '#5F4896', '#22c55e', '#2563eb', '#0C2742']
  return Object.entries(map).map(([label, value], index) => ({
    label,
    value,
    color: colors[index % colors.length],
  }))
}

function buildRollRates(rows: LoanRow[]): RollRateEntry[] {
  const counts: Record<string, Record<string, number>> = {}
  rows.forEach((row) => {
    if (!row.dpd_status) return
    const target = row.loan_status || 'current'
    counts[row.dpd_status] = counts[row.dpd_status] || {}
    counts[row.dpd_status][target] = (counts[row.dpd_status][target] || 0) + 1
  })
  const entries: RollRateEntry[] = []
  Object.entries(counts).forEach(([from, destinations]) => {
    const sum = Object.values(destinations).reduce((sum, value) => sum + value, 0)
    Object.entries(destinations).forEach(([to, value]) => {
      entries.push({
        from,
        to,
        percent: sum ? Number(((value / sum) * 100).toFixed(1)) : 0,
      })
    })
  })
  return entries
}

function buildGrowthProjection(baseYield: number, count: number): GrowthPoint[] {
  const start = baseYield || 1.2
  const loanBase = count || 100
  return Array.from({ length: 6 }).map((_, index) => ({
    label: new Date(Date.now() + index * 30 * 24 * 60 * 60 * 1000).toLocaleString('default', {
      month: 'short',
      year: 'numeric',
    }),
    yield: Number((start + index * 0.15).toFixed(2)),
    loanVolume: loanBase + index * 15,
  }))
}
