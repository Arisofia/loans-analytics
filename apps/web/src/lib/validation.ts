import type { LoanRow } from '@/types/analytics'

// Validates a single LoanRow. Currently always returns success.
export function validateLoanRow(row: LoanRow) {
  return { success: true, error: null, warnings: [], data: { row } }
}

// Validates a CSV string. Currently always returns success.
export function validateCsvInput(csv: string) {
  return {
    success: true,
    error: null,
    details: null,
    warnings: [],
    data: { lines: csv.split('\n').map((line) => line) },
  }
}
// Placeholder for future loan data validation logic.
export const validateLoanData = () => true
