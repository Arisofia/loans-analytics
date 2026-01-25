export const DEMO_DATA = {
  marketing: {
    spend: 5000,
    impressions: 150000,
    clicks: 4500,
    conversions: 120
  },
  kpis: {
    roi: 2.5,
    cac: 45.00,
    ltv: 450.00
  }
};

export function getDemoOrRealValue(realValue: any, demoValue: any) {
  // Return real value if it exists and is not empty/zero, otherwise demo
  if (realValue !== undefined && realValue !== null && realValue !== 0) {
    return realValue;
  }
  return demoValue;
}
