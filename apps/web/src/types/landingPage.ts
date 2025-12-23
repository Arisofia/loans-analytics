import { z } from 'zod'

const metricSchema = z.object({
  label: z.string(),
  value: z.string(),
  helper: z.string().optional(),
})

const productSchema = z.object({
  title: z.string(),
  detail: z.string(),
  kicker: z.string().optional(),
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

export type Metric = Readonly<z.infer<typeof metricSchema>>
export type Product = Readonly<z.infer<typeof productSchema>>
export type Step = Readonly<z.infer<typeof stepSchema>>
export type LandingPageData = Readonly<z.infer<typeof landingPageDataSchema>>

export const EMPTY_LANDING_PAGE_DATA: LandingPageData = Object.freeze(
  landingPageDataSchema.parse({})
)
