// Represents a single entry in a treemap visualization.
export interface TreemapEntry {
  label: string
  value: number
  color?: string
}

// Represents a roll rate transition between loan statuses.
export interface RollRateEntry {
  from: string
  to: string
  percent: number
}

// Represents a point in a loan growth projection.
export interface GrowthPoint {
  label: string
  loanVolume: number
  yield: number
}
export interface Metric {
  id: string
  label: string
  value: number
  change?: number
  trend?: 'up' | 'down' | 'neutral'
}

export interface AnalyticsData {
  metrics: Metric[]
  period: string
}

export interface LoanRow {
  amount?: number
  monto?: number
  principal?: number
  loan_amount?: number
  appraised_value?: number
  borrower_income?: number
  monthly_debt?: number
  status?: string
  estado?: string
  loan_status?: string
  rate?: number
  tasa?: number
  interest_rate?: number
  principal_balance?: number
  dpd_status?: string
    [key: string]: string | number | undefined
}

export interface KPIStats {
  totalVolume: number
  activeLoans: number
  defaultRate: number
  averageRate: number
  delinquencyRate: number
  portfolioYield: number
  loanCount: number
  averageLTV: number
  averageDTI: number
}

export interface ProcessedAnalytics {
  totalVolume: number
  activeLoans: number
  defaultRate: number
  averageRate: number
  delinquencyRate?: number
  portfolioYield?: number
  loanCount?: number
  averageLTV?: number
  averageDTI?: number
  loans?: LoanRow[]
  kpis?: KPIStats
  treemap?: TreemapEntry[]
  rollRates?: RollRateEntry[]
  growthProjection?: GrowthPoint[]
}
