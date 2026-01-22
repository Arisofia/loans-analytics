interface FeatureItem {
  title: string
  detail: string
  kicker?: string
}

export const features: ReadonlyArray<FeatureItem> = [
  {
    title: 'Portfolio Intelligence',
    detail: 'Daily performance lenses across cohorts, pricing, liquidity, and partner flows.',
    kicker: 'Capital efficiency, reserve discipline, and covenant readiness.',
  },
  {
    title: 'Risk & Compliance',
    detail: 'Automated covenant tracking and risk alerts.',
    kicker: 'Proactive risk management.',
  },
]
