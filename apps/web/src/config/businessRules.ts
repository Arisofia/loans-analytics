export const BUSINESS_RULES = {
  delinquentStatuses: [
    '30-59 days past due',
    '60-89 days past due',
    '90+ days past due'
  ],
  uiTheme: {
    chartColors: ['#C1A6FF', '#5F4896', '#22c55e', '#2563eb', '#0C2742'],
    riskColors: {
      high: '#e74c3c',
      medium: '#f39c12',
      low: '#27ae60'
    }
  },
  growthProjections: {
    defaultYield: 1.2,
    monthlyIncrement: 0.15,
    volumeIncrement: 15
  }
}
