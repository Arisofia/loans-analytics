import { validateLoanRow, validateAnalytics, validateCsvInput } from '../../src/lib/validation';
import type { LoanRow } from '../../src/types/analytics';

describe('validateLoanRow', () => {
  it('should validate a valid loan row', () => {
    const validLoan: LoanRow = {
      id: '1',
      loan_amount: 50000,
      appraised_value: 60000,
      borrower_income: 80000,
      monthly_debt: 2000,
      loan_status: 'active',
      interest_rate: 5.5,
      principal_balance: 45000,
      dpd_status: 'current',
    };

    const result = validateLoanRow(validLoan);
    expect(result.success).toBe(true);
  });

  it('should reject loan row with negative loan_amount', () => {
    const invalidLoan = {
      loan_amount: -1000,
      appraised_value: 60000,
      borrower_income: 80000,
      monthly_debt: 2000,
      loan_status: 'active',
      interest_rate: 5.5,
      principal_balance: 45000,
    };

    const result = validateLoanRow(invalidLoan);
    expect(result.success).toBe(false);
  });
});

describe('validateCsvInput', () => {
  it('should validate a valid CSV string with 7+ columns', () => {
    const csv = `loan_id,amount,status,rate,balance,income,debt\n1,50000,active,5.5,45000,80000,2000\n2,60000,paid,6.0,0,90000,1500`;
    const result = validateCsvInput(csv);
    expect(result.success).toBe(true);
  });

  it('should reject CSV with too few columns', () => {
    const csv = `id,amount\n1,50000`;
    const result = validateCsvInput(csv);
    expect(result.success).toBe(false);
  });

  it('should reject empty CSV', () => {
    const result = validateCsvInput('');
    expect(result.success).toBe(false);
  });
});