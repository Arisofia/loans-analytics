// Parses CSV string into LoanRow[] (stub)
import type { LoanRow } from '@/types/analytics'
export function parseLoanCsv(csv: string): LoanRow[] {
  // TODO: Implement real CSV parsing
  return []
}
export function toNumber(value: any): number {
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    // Robust parsing: remove currency symbols, handle commas
    const cleanValue = value.replace(/[^0-9.,-]+/g, '')
    const parsed = parseFloat(cleanValue)
    return isNaN(parsed) ? 0 : parsed
  }
  return 0
}

export function computeKPIs(data: any[]) {
  if (!data || data.length === 0) {
    return {
      totalVolume: 0,
      activeLoans: 0,
      defaultRate: 0,
      averageRate: 0,
      loanCount: 0,
      delinquencyRate: 0,
      portfolioYield: 0,
      averageLTV: 0,
      averageDTI: 0,
    }
  }

  const totalVolume = data.reduce((sum, loan) => sum + toNumber(loan.amount || loan.monto || 0), 0)
  const activeLoans = data.filter((loan) => {
    const s = (loan.status || loan.estado || '').toLowerCase()
    return s === 'active' || s === 'activo' || s === 'current'
  }).length
  const defaultedLoans = data.filter((loan) => {
    const s = (loan.status || loan.estado || '').toLowerCase()
    return s === 'default' || s === 'mora' || s === 'charged_off'
  }).length
  const defaultRate = data.length > 0 ? (defaultedLoans / data.length) * 100 : 0
  const averageRate =
    data.length > 0
      ? data.reduce((sum, loan) => sum + toNumber(loan.rate || 0), 0) / data.length
      : 0
  const loanCount = data.length
  const delinquencyRate = data.length > 0 ? (defaultedLoans / data.length) * 100 : 0
  const portfolioYield =
    data.length > 0
      ? data.reduce((sum, loan) => sum + toNumber(loan.yield || 0), 0) / data.length
      : 0
  const averageLTV =
    data.length > 0 ? data.reduce((sum, loan) => sum + toNumber(loan.ltv || 0), 0) / data.length : 0
  const averageDTI =
    data.length > 0 ? data.reduce((sum, loan) => sum + toNumber(loan.dti || 0), 0) / data.length : 0
  return {
    totalVolume,
    activeLoans,
    defaultRate,
    averageRate,
    loanCount,
    delinquencyRate,
    portfolioYield,
    averageLTV,
    averageDTI,
  }
}
