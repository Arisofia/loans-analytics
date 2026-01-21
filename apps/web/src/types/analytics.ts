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
