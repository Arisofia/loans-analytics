import type { LandingPageData } from '../types/landingPage'

type LandingPageStatus = 'missing-config' | 'fetch-error' | 'no-data' | 'invalid-shape' | 'ok'

type LandingPageDiagnostic = {
  status: LandingPageStatus
  supabaseConfigured: boolean
  metricCount: number
  productCount: number
  controlCount: number
  stepCount: number
  error?: unknown
}

const formatError = (error: unknown) => {
  if (!error) return undefined
  if (error instanceof Error) return error.message
  return typeof error === 'string' ? error : JSON.stringify(error)
}

const summarizePayload = (payload: LandingPageData) => ({
  metricCount: payload.metrics.length,
  productCount: payload.products.length,
  controlCount: payload.controls.length,
  stepCount: payload.steps.length,
})

export const logLandingPageDiagnostic = (
  diagnostic: Omit<
    LandingPageDiagnostic,
    'metricCount' | 'productCount' | 'controlCount' | 'stepCount'
  > & {
    payload: LandingPageData
  }
) => {
  const counts = summarizePayload(diagnostic.payload)
  const output: LandingPageDiagnostic = {
    status: diagnostic.status,
    supabaseConfigured: diagnostic.supabaseConfigured,
    error: formatError(diagnostic.error),
    ...counts,
  }

  if (diagnostic.status === 'ok') {
    console.warn('Landing page data diagnostic', output)
    return
  }

  console.error('Landing page data diagnostic', output)
}
