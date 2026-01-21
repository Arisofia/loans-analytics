export interface TreemapEntry {
  label: string
  value: number
  color?: string
}

export interface RollRateEntry {
  from: string
  to: string
  percent: number
}

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
  status?: string
  estado?: string
  rate?: number
  tasa?: number
  interest_rate?: number
  [key: string]: any
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
