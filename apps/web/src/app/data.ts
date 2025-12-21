import type { Metric, Product, Step } from '../types/landingPage'

export type MarketingContent = {
  readonly metrics: readonly Metric[]
  readonly products: readonly Product[]
  readonly controls: readonly string[]
  readonly steps: readonly Step[]
}

export const metrics = [
  { label: 'Approval uplift with governed risk', value: '+18%', helper: 'QoQ across prime and near-prime' },
  { label: 'Reduction in manual reviews', value: '42%', helper: 'Workflow automation with auditability' },
  { label: 'Portfolio coverage with audit trails', value: '100%', helper: 'Evidence mapped to every decision' },
] as const satisfies readonly Metric[]

export const products = [
  {
    title: 'Portfolio Intelligence',
    detail: 'Daily performance lenses across cohorts, pricing, liquidity, and partner flows.',
    kicker: 'Capital efficiency, reserve discipline, and covenant readiness.',
  },
  {
    title: 'Risk Orchestration',
    detail: 'Dynamic policy controls, challenger experiments, and guardrails to defend credit quality.',
    kicker: 'Segregation of duties with sign-offs and immutable change logs.',
  },
  {
    title: 'Growth Enablement',
    detail: 'Pre-approved journeys, partner-ready APIs, and data rooms that accelerate funding decisions.',
    kicker: 'Unified evidence packs for investors, auditors, and strategic partners.',
  },
] as const satisfies readonly Product[]

export const controls = [
  'Segregated roles, approvals, and immutable audit logs for every change.',
  'Real-time monitoring of SLAs, risk thresholds, and operational KPIs.',
  'Encryption by default with least-privilege access across environments.',
  'Continuous evidence packs for regulators, investors, and funding partners.',
] as const satisfies readonly string[]

export const steps = [
  { label: '01', title: 'Unify data signals', copy: 'Blend bureau, behavioral, and operational streams into a trusted lending graph.' },
  { label: '02', title: 'Govern decisions', copy: 'Codify policies with traceable approvals, challenger tests, and audit logs.' },
  { label: '03', title: 'Accelerate growth', copy: 'Launch pre-approved journeys, partner APIs, and KPI packs for capital partners.' },
] as const satisfies readonly Step[]

export const marketingContent: MarketingContent = {
  metrics,
  products,
  controls,
  steps,
}

export type { MarketingContent }
