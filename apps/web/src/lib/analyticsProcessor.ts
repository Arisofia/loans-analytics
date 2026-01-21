import {
  LoanRow,
  ProcessedAnalytics,
  RollRateEntry,
  TreemapEntry,
  GrowthPoint,
} from '@/types/analytics'

const currencyRegex = /[^\d.-]/g

export function toNumber(value: any): number {
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    // Elimina símbolos de moneda y comas, luego convierte
    const cleanValue = value.replace(/[^0-9.-]+/g, '')
    const parsed = parseFloat(cleanValue)
    return isNaN(parsed) ? 0 : parsed
  }
  return 0
}

type LoanCsvRecord = Record<string, string>

export function parseLoanCsv(content: string): LoanRow[] {
  const rows = content
    .trim()
    .split(/\r?\n/)
    .map((line) =>
      // Split by comma, ignoring commas inside double quotes
      line.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/).map((val) => val.trim().replace(/^"|"$/g, '').replace(/""/g, '"'))
    )
    .filter((parts) => parts.length >= 7)

  const header = rows.shift()
  if (!header) return []

  const keys = header.map((col) => col.trim().toLowerCase())

  const toRecord = (parts: string[]): LoanCsvRecord =>
    parts.reduce<LoanCsvRecord>((acc, value, index) => {
      const key = keys[index] ?? `col_${index}`
      acc[key] = value.trim()
      return acc
    }, {})

  return rows.map((parts) => {
    const record = toRecord(parts)
    const getField = (key: string) => record[key] ?? ''
    return {
      loan_amount: toNumber(getField('loan_amount')),
      appraised_value: toNumber(getField('appraised_value')),
      borrower_income: toNumber(getField('borrower_income')),
      monthly_debt: toNumber(getField('monthly_debt')),
      loan_status: getField('loan_status') || 'unknown',
      interest_rate: toNumber(getField('interest_rate')),
      principal_balance: toNumber(getField('principal_balance')),
      dpd_status: getField('dpd_status') || '',
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
  }
}

export function computeKPIs(data: any[]) {
  if (!data || data.length === 0) {
    return {
      totalVolume: 0,
      activeLoans: 0,
      defaultRate: 0,
      averageRate: 0,
    }
  }

  // Lógica Real: Sumar el monto de los préstamos (asumiendo campo 'amount' o 'monto')
  const totalVolume = data.reduce((sum, loan) => {
    return sum + toNumber(loan.amount || loan.monto || 0)
  }, 0)

  const activeLoans = data.filter(
    (loan) => loan.status === 'active' || loan.estado === 'activo'
  ).length

  // Cálculo simple de tasa de default (ejemplo)
  const defaultedLoans = data.filter(
    (loan) => loan.status === 'default' || loan.estado === 'mora'
  ).length

  const defaultRate = activeLoans > 0 ? (defaultedLoans / data.length) * 100 : 0

  return {
    totalVolume,
    activeLoans,
    defaultRate,
    averageRate: 0, // Implementar según tus campos de interés
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
