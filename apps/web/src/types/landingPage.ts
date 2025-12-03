export interface Metric {
  value: string
  label: string
}

export interface Product {
  title: string
  detail: string
}

export interface Step {
  label: string
  title: string
  copy: string
}

export interface LandingPageData {
  metrics: Metric[]
  products: Product[]
  controls: string[]
  steps: Step[]
}
