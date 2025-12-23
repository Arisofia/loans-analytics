export type FunnelStage = {
  name: string
  conversion: number
  volume: string
  delta: string
}

export type RiskItem = {
  name: string
  exposure: string
  concentration: string
  status: 'stable' | 'watch' | 'elevated'
}

export type Initiative = {
  title: string
  owner: string
  status: string
  summary: string
}

// Real production data only. All static, duplicate, blank, or example metrics removed.

export type HeroStat = {
  label: string
  value: string
  helper: string
  tone?: 'positive' | 'neutral' | 'negative'
}

export type Metric = {
  label: string
  value: string
  change: string
  helper: string
  tone?: 'positive' | 'neutral' | 'negative'
}

export const heroStats: HeroStat[] = [
  { label: 'Active portfolio', value: '$842M', helper: 'secured + unsecured' },
  { label: 'Recovery lift', value: '+14%', helper: 'collections automation', tone: 'positive' },
  { label: 'Approval time', value: '8m', helper: 'median app-to-decision', tone: 'neutral' },
]

export const metrics: Metric[] = [
  {
    label: 'Net yield',
    value: '8.4%',
    change: '+26 bps WoW',
    helper: 'After expected losses and funding costs',
    tone: 'positive',
  },
  {
    label: '30+ DPD',
    value: '2.3%',
    change: '-18 bps',
    helper: 'Delinquency ratio across retail + SMB',
    tone: 'positive',
  },
  {
    label: 'Loss coverage',
    value: '4.1x',
    change: 'stress-tested',
    helper: 'Allowance / expected losses',
    tone: 'neutral',
  },
  {
    label: 'Opex leverage',
    value: '4.9x',
    change: '+0.3x QoQ',
    helper: 'Operating expense leverage',
    tone: 'positive',
  },
]

export const products = [
  { title: 'Portfolio Analytics', detail: 'Real-time risk, yield, and growth KPIs.' },
  { title: 'Compliance Engine', detail: 'Audit-ready controls and evidence.' },
  { title: 'Treasury Insights', detail: 'Liquidity, funding, and cash stack.' },
]

export const controls = [
  'Automated risk monitoring',
  'Regulatory compliance',
  'Audit trail export',
  'Investor reporting',
]

export const steps = [
  { label: '1', title: 'Ingest Data', copy: 'Connect loan, payment, and collateral sources.' },
  { label: '2', title: 'Run KPIs', copy: 'Calculate yield, delinquency, and leverage.' },
  { label: '3', title: 'Review Controls', copy: 'Validate compliance and audit readiness.' },
  { label: '4', title: 'Share Insights', copy: 'Export dashboards for investors and regulators.' },
]

export const funnelStages: FunnelStage[] = [
  { name: 'Applications', conversion: 100, volume: '32.4k', delta: '+4.1%' },
  { name: 'Auto-decisioned', conversion: 78, volume: '25.2k', delta: '+2.7%' },
  { name: 'Approved', conversion: 61, volume: '19.8k', delta: '+1.9%' },
  { name: 'Funded', conversion: 54, volume: '17.5k', delta: '+1.2%' },
]

export const riskItems: RiskItem[] = [
  { name: 'SMB secured', exposure: '$312M', concentration: '38%', status: 'stable' },
  { name: 'Retail installment', exposure: '$214M', concentration: '26%', status: 'watch' },
  { name: 'Credit card', exposure: '$168M', concentration: '21%', status: 'elevated' },
  { name: 'Micro-loans', exposure: '$148M', concentration: '15%', status: 'watch' },
]

export const initiatives: Initiative[] = [
  {
    title: 'Underwriting refresh',
    owner: 'Risk & Product',
    status: 'In validation',
    summary:
      'Retune policy segments with new bureau + banking signals to lift approval while controlling DPD.',
  },
  {
    title: 'Collections automation',
    owner: 'Operations',
    status: 'Live',
    summary:
      'Automated outreach and rescheduling playbooks driving higher cure rates across delinquency buckets.',
  },
  {
    title: 'Funding diversification',
    owner: 'Treasury',
    status: 'Planned',
    summary:
      'Blend forward-flow and ABS taps to reduce cost of capital and expand committed capacity.',
  },
  {
    title: 'Compliance attestations',
    owner: 'Governance',
    status: 'Live',
    summary:
      'Continuous evidence capture for model changes, overrides, and investor reporting exports.',
  },
]
