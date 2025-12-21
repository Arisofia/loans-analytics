import type { LandingPageData, Metric, Product, Step } from '../types/landingPage'

export const metrics: Metric[] = [
  { label: 'Approval uplift with governed risk', value: '+18%', helper: 'QoQ across prime and near-prime' },
  { label: 'Reduction in manual reviews', value: '42%', helper: 'Workflow automation with auditability' },
  { label: 'Portfolio coverage with audit trails', value: '100%', helper: 'Evidence mapped to every decision' },
]

export const products: Product[] = [
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
]

export const controls: string[] = [
  'Segregated roles, approvals, and immutable audit logs for every change.',
  'Real-time monitoring of SLAs, risk thresholds, and operational KPIs.',
  'Encryption by default with least-privilege access across environments.',
  'Continuous evidence packs for regulators, investors, and funding partners.',
]

export const steps: Step[] = [
  { label: '01', title: 'Unify data signals', copy: 'Blend credit bureau, behavioral, and operational streams to build a trusted lending graph.' },
  { label: '02', title: 'Model & decide', copy: 'Score applicants with explainable risk layers and adaptive policies aligned to appetite.' },
  { label: '03', title: 'Measure & learn', copy: 'Track outcomes against revenue and risk KPIs, iterating with governed experiment loops.' },
]

export const marketingContent: LandingPageData = {
  metrics,
  products,
  controls,
  steps,
}
