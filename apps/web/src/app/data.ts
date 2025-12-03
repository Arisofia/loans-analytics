<<<<<<< HEAD
export type Metric = {
  label: string
  value: string
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
=======
export type Metric = Readonly<{
  label: string
  value: string
}>

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
>>>>>>> origin/main
  { label: 'Approval uplift with governed risk', value: '+18%' },
  { label: 'Reduction in manual reviews', value: '42%' },
  { label: 'Portfolio coverage with audit trails', value: '100%' },
]

<<<<<<< HEAD
export const products: Product[] = [
=======
export const products: ReadonlyArray<Product> = [
>>>>>>> origin/main
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
]

<<<<<<< HEAD
export const controls: string[] = [
=======
export const controls: ReadonlyArray<string> = [
>>>>>>> origin/main
  'Segregated roles, approvals, and immutable audit logs for every change.',
  'Real-time monitoring of SLAs, risk thresholds, and operational KPIs.',
  'Encryption by default with least-privilege access across environments.',
]

<<<<<<< HEAD
export const steps: Step[] = [
=======
export const steps: ReadonlyArray<Step> = [
>>>>>>> origin/main
  {
    label: '01',
    title: 'Unify data signals',
    copy: 'Blend credit bureau, behavioral, and operational streams to build a trusted lending graph.',
  },
  {
    label: '02',
    title: 'Model & decide',
    copy: 'Score applicants with explainable risk layers and adaptive policies aligned to appetite.',
  },
  {
    label: '03',
    title: 'Measure & learn',
    copy: 'Track outcomes against revenue and risk KPIs, iterating with governed experiment loops.',
  },
]
