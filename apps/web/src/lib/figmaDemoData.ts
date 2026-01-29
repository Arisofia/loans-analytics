/**
 * Demo data for Figma marketing dashboard exports
 * Used when backend data is unavailable or incomplete
 */

export const DEMO_DATA = {
  unit_economics: [
    { month: '2024-07', cac_usd: 280, ltv_realized: 920, ltv_cac_ratio: 3.29 },
    { month: '2024-08', cac_usd: 275, ltv_realized: 940, ltv_cac_ratio: 3.42 },
    { month: '2024-09', cac_usd: 270, ltv_realized: 955, ltv_cac_ratio: 3.54 },
    { month: '2024-10', cac_usd: 265, ltv_realized: 970, ltv_cac_ratio: 3.66 },
    { month: '2024-11', cac_usd: 260, ltv_realized: 980, ltv_cac_ratio: 3.77 },
    { month: '2024-12', cac_usd: 255, ltv_realized: 990, ltv_cac_ratio: 3.88 },
  ],

  customer_types: [
    { type: 'New', count: 45, percentage: 13.8 },
    { type: 'Recurrent', count: 240, percentage: 73.4 },
    { type: 'Recovered', count: 42, percentage: 12.8 },
  ],

  customer_classification: [
    { segment: 'Premium', count: 82, percentage: 25.1 },
    { segment: 'Standard', count: 180, percentage: 55.0 },
    { segment: 'Basic', count: 65, percentage: 19.9 },
  ],

  churn_90d_metrics: [
    { month: '2024-07', churn90d_pct: 8.2, active_90d: 365, inactive_90d: 12, churn_dollar: 7200 },
    { month: '2024-08', churn90d_pct: 7.8, active_90d: 370, inactive_90d: 10, churn_dollar: 6800 },
    { month: '2024-09', churn90d_pct: 7.5, active_90d: 372, inactive_90d: 9, churn_dollar: 6600 },
    { month: '2024-10', churn90d_pct: 7.3, active_90d: 375, inactive_90d: 9, churn_dollar: 6500 },
    { month: '2024-11', churn90d_pct: 7.2, active_90d: 378, inactive_90d: 8, churn_dollar: 6400 },
    { month: '2024-12', churn90d_pct: 7.0, active_90d: 380, inactive_90d: 8, churn_dollar: 6300 },
  ],

  intensity_segmentation: [
    { intensity: 'High', count: 95, percentage: 29.1 },
    { intensity: 'Medium', count: 165, percentage: 50.5 },
    { intensity: 'Low', count: 67, percentage: 20.4 },
  ],

  line_size_segmentation: [
    { size: 'Large (>$10K)', count: 45, percentage: 13.8 },
    { size: 'Medium ($5K-$10K)', count: 120, percentage: 36.7 },
    { size: 'Small (<$5K)', count: 162, percentage: 49.5 },
  ],

  average_ticket: [
    { band: '$0-$1K', count: 45, percentage: 13.8 },
    { band: '$1K-$3K', count: 130, percentage: 39.8 },
    { band: '$3K-$5K', count: 95, percentage: 29.1 },
    { band: '$5K+', count: 57, percentage: 17.4 },
  ],

  figma_dashboard: [
    { month: '2024-07', disbursements: 3800000, growth_mom: 2.5, growth_yoy: 15.2 },
    { month: '2024-08', disbursements: 3900000, growth_mom: 2.6, growth_yoy: 14.8 },
    { month: '2024-09', disbursements: 3950000, growth_mom: 1.3, growth_yoy: 12.5 },
    { month: '2024-10', disbursements: 4000000, growth_mom: 1.3, growth_yoy: 11.2 },
    { month: '2024-11', disbursements: 3950000, growth_mom: -1.3, growth_yoy: 8.5 },
    { month: '2024-12', disbursements: 3974478, growth_mom: 0.6, growth_yoy: 6.2 },
  ],

  monthly_pricing: [
    { month: '2024-07', weighted_apr: 76.5, weighted_fee: 4.8, recurrence_pct: 55.2 },
    { month: '2024-08', weighted_apr: 77.0, weighted_fee: 4.85, recurrence_pct: 56.1 },
    { month: '2024-09', weighted_apr: 77.5, weighted_fee: 4.87, recurrence_pct: 57.0 },
    { month: '2024-10', weighted_apr: 77.8, weighted_fee: 4.88, recurrence_pct: 57.5 },
    { month: '2024-11', weighted_apr: 78.0, weighted_fee: 4.9, recurrence_pct: 58.0 },
    { month: '2024-12', weighted_apr: 78.1, weighted_fee: 4.9, recurrence_pct: 58.4 },
  ],

  payment_timing: [
    { timing: 'Early (>5 days)', count: 85, percentage: 26.0 },
    { timing: 'On-time (0-5 days)', count: 180, percentage: 55.0 },
    { timing: 'Late (1-30 days)', count: 45, percentage: 13.8 },
    { timing: 'Delinquent (>30 days)', count: 17, percentage: 5.2 },
  ],

  collection_rate: [
    { month: '2024-07', rate: 94.5 },
    { month: '2024-08', rate: 94.8 },
    { month: '2024-09', rate: 95.0 },
    { month: '2024-10', rate: 95.2 },
    { month: '2024-11', rate: 95.3 },
    { month: '2024-12', rate: 95.5 },
  ],

  concentration: [
    { month: '2024-07', top_10_pct: 28.5, top_20_pct: 42.3 },
    { month: '2024-08', top_10_pct: 27.8, top_20_pct: 41.5 },
    { month: '2024-09', top_10_pct: 27.2, top_20_pct: 40.8 },
    { month: '2024-10', top_10_pct: 26.8, top_20_pct: 40.2 },
    { month: '2024-11', top_10_pct: 26.5, top_20_pct: 39.8 },
    { month: '2024-12', top_10_pct: 26.2, top_20_pct: 39.5 },
  ],

  monthly_risk: [
    { month: '2024-07', dpd_30_pct: 5.2, dpd_60_pct: 2.1, dpd_90_pct: 0.8 },
    { month: '2024-08', dpd_30_pct: 5.0, dpd_60_pct: 2.0, dpd_90_pct: 0.7 },
    { month: '2024-09', dpd_30_pct: 4.8, dpd_60_pct: 1.9, dpd_90_pct: 0.7 },
    { month: '2024-10', dpd_30_pct: 4.6, dpd_60_pct: 1.8, dpd_90_pct: 0.6 },
    { month: '2024-11', dpd_30_pct: 4.5, dpd_60_pct: 1.7, dpd_90_pct: 0.6 },
    { month: '2024-12', dpd_30_pct: 4.3, dpd_60_pct: 1.6, dpd_90_pct: 0.5 },
  ],
}

/**
 * Returns real data if available and non-empty, otherwise returns demo data
 * @param realData - The real data from the backend
 * @param demoData - The fallback demo data
 * @returns The real data if valid, otherwise the demo data
 */
export function getDemoOrRealValue<T>(
  realData: T[] | undefined | null,
  demoData: T[]
): T[] {
  if (realData && Array.isArray(realData) && realData.length > 0) {
    return realData
  }
  return demoData
}
