/**
 * Minimal placeholder for landing page diagnostics.
 * Replace implementations with your real telemetry/logging.
 */

export function logLandingPageDiagnostic(event: unknown, data?: Record<string, unknown>) {
  // No-op for build. In production, replace with real logging.
  if (process.env.NODE_ENV !== 'production') {
    // eslint-disable-next-line no-console
    console.debug('[landingDiagnostic]', event, data ?? {});
  }
}
