export type Metric = {
  label: string
  value: string
  helper?: string
}

export type Product = {
  title: string
  detail: string
  kicker?: string
}

export type Step = {
  label: string
  title: string
  copy: string
}

export type LandingPageData = {
  metrics: Metric[]
  products: Product[]
  steps: Step[]
  controls: string[]
}

export const EMPTY_LANDING_PAGE_DATA: LandingPageData = {
  metrics: [],
  products: [],
  steps: [],
  controls: [],
}
