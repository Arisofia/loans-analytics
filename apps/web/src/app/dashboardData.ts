// Static data for the fintech analytics landing page

export type Metric = {
  label: string
  value: string
  helper?: string
}

export type Product = {
  title: string
  detail: string
}

export type Step = {
  label: string
  title: string
  copy: string
}

export const metrics: Metric[] = [
  { label: 'Yield', value: '8.2%', helper: 'Net portfolio yield' },
  { label: 'Delinquency', value: '2.1%', helper: '30+ DPD ratio' },
  { label: 'Operating Leverage', value: '4.7x', helper: 'Revenue / Opex' },
]

export const products: Product[] = [
  { title: 'Portfolio Analytics', detail: 'Real-time risk, yield, and growth KPIs.' },
  { title: 'Compliance Engine', detail: 'Audit-ready controls and evidence.' },
  { title: 'Treasury Insights', detail: 'Liquidity, funding, and cash stack.' },
]

export const controls: string[] = [
  'Automated risk monitoring',
  'Regulatory compliance',
  'Audit trail export',
  'Investor reporting',
]

export const steps: Step[] = [
  { label: '1', title: 'Ingest Data', copy: 'Connect loan, payment, and collateral sources.' },
  { label: '2', title: 'Run KPIs', copy: 'Calculate yield, delinquency, and leverage.' },
  { label: '3', title: 'Review Controls', copy: 'Validate compliance and audit readiness.' },
  { label: '4', title: 'Share Insights', copy: 'Export dashboards for investors and regulators.' },
]
