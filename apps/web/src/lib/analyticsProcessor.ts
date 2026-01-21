import { type Metric } from '@/types/analytics';

export function toNumber(value: any): number {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    // Robust parsing: remove currency symbols, handle commas
    const cleanValue = value.replace(/[^0-9.-]+/g, "");
    const parsed = parseFloat(cleanValue);
    return isNaN(parsed) ? 0 : parsed;
  }
  return 0;
}

export function computeKPIs(data: any[]) {
  if (!data || data.length === 0) {
    return {
      totalVolume: 0,
      activeLoans: 0,
      defaultRate: 0,
      averageRate: 0
    };
  }

  const totalVolume = data.reduce((sum, loan) => {
    return sum + toNumber(loan.amount || loan.monto || 0);
  }, 0);

  const activeLoans = data.filter(loan => {
    const s = (loan.status || loan.estado || '').toLowerCase();
    return s === 'active' || s === 'activo' || s === 'current';
  }).length;

  const defaultedLoans = data.filter(loan => {
    const s = (loan.status || loan.estado || '').toLowerCase();
    return s === 'default' || s === 'mora' || s === 'charged_off';
  }).length;
  
  const defaultRate = data.length > 0 ? (defaultedLoans / data.length) * 100 : 0;

  const totalRate = data.reduce((sum, loan) => {
    return sum + toNumber(loan.rate || loan.tasa || loan.interest_rate || 0);
  }, 0);
  
  const averageRate = data.length > 0 ? totalRate / data.length : 0;

  return { totalVolume, activeLoans, defaultRate, averageRate };
}
