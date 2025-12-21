import type { Metric } from '../types/landingPage'

export type ProductType = Readonly<{
  title: string
  detail: string
}>

export type StepType = Readonly<{
  label: string
  title: string
  copy: string
}>

export const metrics: ReadonlyArray<Metric> = [
  { label: 'Approval uplift with governed risk', value: '+18%' },
  { label: 'Reduction in manual reviews', value: '42%' },
  { label: 'Portfolio coverage with audit trails', value: '100%' },
] as const satisfies readonly Metric[]

export const products: readonly ProductType[] = [
  {
    title: 'Portfolio Intelligence',
    detail: 'Daily performance lenses across cohorts, pricing, liquidity, and partner flows.',
  },
  {
    title: 'Risk Orchestration',
    detail: 'Dynamic policy controls, challenger experiments, and guardrails to defend credit quality.',
  },
  {
    title: 'Growth Enablement',
    detail: 'Pre-approved journeys, partner-ready APIs, and data rooms that accelerate funding decisions.',
  },
] as const satisfies readonly ProductType[]

export const controls: readonly string[] = [
  'Segregated roles, approvals, and immutable audit logs for every change.',
  'Real-time monitoring of SLAs, risk thresholds, and operational KPIs.',
  'Encryption by default with least-privilege access across environments.',
  'Continuous evidence packs for regulators, investors, and funding partners.',
] as const satisfies readonly string[]

export const steps: ReadonlyArray<StepType> = [
  {
    label: '01',
    title: 'Unify data signals',
    copy: 'Blend credit bureau, behavioral, and operational streams to build a trusted lending graph.',
  },
  {
    label: '02',
    title: 'Govern decisions',
    copy: 'Codify policies with traceable approvals, challenger tests, and audit logs.',
  },
  {
    label: '03',
    title: 'Accelerate growth',
    copy: 'Launch pre-approved journeys, partner APIs, and KPI packs for capital partners.',
  },
] as const satisfies readonly StepType[]

export type MarketingContent = {
  readonly metrics: readonly Metric[]
  readonly products: readonly ProductType[]
  readonly controls: readonly string[]
  readonly steps: readonly StepType[]
}

export const marketingContent: MarketingContent = {
  metrics,
  products,
  controls,
  steps,
}
