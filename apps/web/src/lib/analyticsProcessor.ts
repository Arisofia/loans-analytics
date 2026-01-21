export function computeKPIs(data: any) {
  // Placeholder logic to satisfy build
  return {
    totalVolume: 0,
    activeLoans: 0,
    defaultRate: 0
  };
}

export function toNumber(value: any): number {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    const parsed = parseFloat(value.replace(/[^0-9.-]+/g, ""));
    return isNaN(parsed) ? 0 : parsed;
  }
  return 0;
}
