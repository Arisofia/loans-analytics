export interface Metric {
  id: string;
  label: string;
  value: number;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
}

export interface AnalyticsData {
  metrics: Metric[];
  period: string;
}

export interface LoanRow {
  amount?: number;
  monto?: number;
  principal?: number;
  status?: string;
  estado?: string;
  rate?: number;
  tasa?: number;
  interest_rate?: number;
  [key: string]: any;
}

export interface ProcessedAnalytics {
  totalVolume: number;
  activeLoans: number;
  defaultRate: number;
  averageRate: number;
  portfolioYield?: number;
  loanCount?: number;
}

export interface RollRateEntry {
  category: string;
  value: number;
}

export interface TreemapEntry {
  name: string;
  value: number;
}

export interface GrowthPoint {
  date: string;
  value: number;
}
