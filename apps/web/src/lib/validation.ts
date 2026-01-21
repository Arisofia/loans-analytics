import type { LoanRow } from '@/types/analytics'

export function validateLoanRow(row: LoanRow) {
  // Stub: always valid
  return { success: true, error: null, warnings: [], data: { row } }
}

export function validateCsvInput(csv: string) {
  // Stub: always valid
  return {
    success: true,
    error: null,
    details: null,
    warnings: [],
    data: { lines: csv.split('\n').map((line) => line) },
  }
}
export const validateLoanData = () => true
