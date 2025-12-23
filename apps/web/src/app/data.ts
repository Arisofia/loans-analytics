export type Metric = Readonly<{
  label: string
  value: string
}>

<<<<<<< HEAD
export const metrics: ReadonlyArray<Metric> = [
  { label: 'Approval uplift with governed risk', value: '+18%', helper: 'QoQ across prime and near-prime' },
  { label: 'Reduction in manual reviews', value: '42%', helper: 'Workflow automation with auditability' },
  { label: 'Portfolio coverage with audit trails', value: '100%', helper: 'Evidence mapped to every decision' },
=======
export type Product = Readonly<{
  title: string
  detail: string
}>

export type Step = Readonly<{
  label: string
  title: string
  copy: string
}>

export const metrics: ReadonlyArray<Metric> = [
  { label: 'Approval uplift with governed risk', value: '+18%' },
  { label: 'Reduction in manual reviews', value: '42%' },
  { label: 'Portfolio coverage with audit trails', value: '100%' },
>>>>>>> origin/main
] as const satisfies readonly Metric[]

export const products: ReadonlyArray<Product> = [
  {
    title: 'Portfolio Intelligence',
    detail:
      'Daily performance lenses across cohorts, pricing, and liquidity to unlock resilient margins.',
  },
  {
    title: 'Risk Orchestration',
    detail:
      'Dynamic policy controls, challenger experiments, and guardrails to defend credit quality.',
  },
  {
    title: 'Growth Enablement',
    detail:
      'Pre-approved journeys, partner-ready APIs, and data rooms that accelerate funding decisions.',
  },
] as const satisfies readonly Product[]

<<<<<<< HEAD
export const steps: ReadonlyArray<Step> = [
  { label: '01', title: 'Unify data signals', copy: 'Blend bureau, behavioral, and operational streams into a trusted lending graph.' },
  { label: '02', title: 'Govern decisions', copy: 'Codify policies with traceable approvals, challenger tests, and audit logs.' },
  { label: '03', title: 'Accelerate growth', copy: 'Launch pre-approved journeys, partner APIs, and KPI packs for capital partners.' },
] as const satisfies readonly Step[]

=======
>>>>>>> origin/main
export const controls: ReadonlyArray<string> = [
  'Segregated roles, approvals, and immutable audit logs for every change.',
  'Real-time monitoring of SLAs, risk thresholds, and operational KPIs.',
  'Encryption by default with least-privilege access across environments.',
<<<<<<< HEAD
  'Continuous evidence packs for regulators, investors, and funding partners.',
=======
>>>>>>> origin/main
] as const satisfies readonly string[]

export type MarketingContent = {
  readonly metrics: readonly Metric[]
  readonly products: readonly Product[]
  readonly controls: readonly string[]
  readonly steps: readonly Step[]
}

export const marketingContent: MarketingContent = {
  metrics,
  products,
  controls,
  steps,
}
