import type { LoanRow } from '@/types/analytics'

export type IdentifiedLoanRow = LoanRow & { id: string }

function buildStableId(index: number) {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `loan-${index}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function ensureLoanIds(rows: LoanRow[]): IdentifiedLoanRow[] {
  return rows.map((row, index) => {
    const existingId = row.id
    return {
      ...row,
      id: existingId ?? buildStableId(index),
    }
  })
}

export function updateLoanById(
  rows: IdentifiedLoanRow[],
  updated: Partial<Omit<IdentifiedLoanRow, 'id'>> & { id: string },
  fallbackIndex?: number
): IdentifiedLoanRow[] {
  const targetIndex = rows.findIndex((row) => row.id === updated.id)
  if (targetIndex !== -1) {
    return rows.map((row, index) => (index === targetIndex ? { ...row, ...updated, id: row.id } : row))
  }

  if (fallbackIndex !== undefined && fallbackIndex >= 0 && fallbackIndex < rows.length) {
    return rows.map((row, index) => (index === fallbackIndex ? { ...row, ...updated, id: row.id ?? updated.id } : row))
  }

  return rows
}
