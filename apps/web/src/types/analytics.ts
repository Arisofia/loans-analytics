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
// Represents a single metric value for analytics.
export interface Metric {
  id: string
  label: string
  value: number
  change?: number
  trend?: 'up' | 'down' | 'neutral'
}

// Container for a set of metrics for a given period.
export interface AnalyticsData {
  metrics: Metric[]
  period: string
}

// Represents a single loan record, with flexible field names for compatibility.
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

// Key performance indicators for a loan portfolio.
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

// Aggregated analytics results for a loan portfolio.
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
