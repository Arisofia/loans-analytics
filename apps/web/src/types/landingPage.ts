<<<<<<< HEAD
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
=======
import { z } from 'zod'

const metricSchema = z.object({
  value: z.string(),
  label: z.string(),
})

const productSchema = z.object({
  title: z.string(),
  detail: z.string(),
})

const stepSchema = z.object({
  label: z.string(),
  title: z.string(),
  copy: z.string(),
})

export const landingPageDataSchema = z.object({
  metrics: z.array(metricSchema).default([]),
  products: z.array(productSchema).default([]),
  controls: z.array(z.string()).default([]),
  steps: z.array(stepSchema).default([]),
})

export type Metric = z.infer<typeof metricSchema>
export type Product = z.infer<typeof productSchema>
export type Step = z.infer<typeof stepSchema>
export type LandingPageData = z.infer<typeof landingPageDataSchema>

export const EMPTY_LANDING_PAGE_DATA: LandingPageData = Object.freeze(
  landingPageDataSchema.parse({})
)
>>>>>>> main
