import { z } from 'zod'
import type { LoanRow, ProcessedAnalytics, KPIStats } from '@/types/analytics'

export type ValidationResult<T> =
  | { success: true; data: T; warnings: string[] }
  | { success: false; error: string; details: Record<string, unknown> }

export const LoanRowSchema = z.object({
  id: z.string().optional(),
  loan_amount: z.number().positive('Loan amount must be positive'),
  appraised_value: z.number().positive('Appraised value must be positive'),
  borrower_income: z.number().nonnegative('Borrower income cannot be negative'),
  monthly_debt: z.number().nonnegative('Monthly debt cannot be negative'),
  loan_status: z.string().min(1, 'Loan status required'),
  interest_rate: z
    .number()
    .min(0, 'Interest rate cannot be negative')
    .max(100, 'Interest rate cannot exceed 100%'),
  principal_balance: z.number().nonnegative('Principal balance cannot be negative'),
  dpd_status: z.string().optional(),
}) satisfies z.ZodType<LoanRow>

export const KPIStatsSchema = z.object({
  delinquencyRate: z.number().min(0).max(100),
  portfolioYield: z.number().min(0).max(100),
  averageLTV: z.number().min(0).max(200),
  averageDTI: z.number().min(0).max(300),
  loanCount: z.number().nonnegative().int(),
}) satisfies z.ZodType<KPIStats>

export const ProcessedAnalyticsSchema = z.object({
  kpis: KPIStatsSchema,
  treemap: z.array(
    z.object({
      label: z.string(),
      value: z.number().nonnegative(),
      color: z.string(),
    })
  ),
  rollRates: z.array(
    z.object({
      from: z.string(),
      to: z.string(),
      percent: z.number().min(0).max(100),
    })
  ),
  growthProjection: z.array(
    z.object({
      label: z.string(),
      yield: z.number().min(0),
      loanVolume: z.number().nonnegative().int(),
    })
  ),
  loans: z.array(LoanRowSchema),
}) satisfies z.ZodType<ProcessedAnalytics>

export function validateLoanRow(row: unknown): ValidationResult<LoanRow> {
  try {
    const data = LoanRowSchema.parse(row)
    return { success: true, data, warnings: [] }
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: 'Invalid loan row',
        details: {
          issues: error.issues.map((issue) => ({
            path: issue.path.join('.'),
            message: issue.message,
            code: issue.code,
          })),
        },
      }
    }
    return {
      success: false,
      error: 'Unknown error during validation',
      details: { error: String(error) },
    }
  }
}

export function validateAnalytics(data: unknown): ValidationResult<ProcessedAnalytics> {
  try {
    const validated = ProcessedAnalyticsSchema.parse(data)
    const warnings: string[] = []

    if (validated.loans.length === 0) {
      warnings.push('No loans provided')
    }

    if (validated.treemap.length === 0) {
      warnings.push('Treemap is empty - no loan statuses found')
    }

    if (validated.rollRates.length === 0) {
      warnings.push('Roll rates are empty - no DPD status data found')
    }

    if (validated.kpis.loanCount === 0) {
      warnings.push('Loan count is zero')
    }

    return { success: true, data: validated, warnings }
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: 'Invalid analytics data',
        details: {
          issues: error.issues.map((issue) => ({
            path: issue.path.join('.'),
            message: issue.message,
            code: issue.code,
          })),
        },
      }
    }
    return {
      success: false,
      error: 'Unknown error during validation',
      details: { error: String(error) },
    }
  }
}

export function validateCsvInput(content: string): ValidationResult<{
  lines: string[]
  columnCount: number
}> {
  if (!content || typeof content !== 'string') {
    return {
      success: false,
      error: 'CSV content must be a non-empty string',
      details: { contentType: typeof content },
    }
  }

  const maxSize = 50 * 1024 * 1024
  if (content.length > maxSize) {
    return {
      success: false,
      error: `CSV file exceeds maximum size of ${maxSize / 1024 / 1024}MB`,
      details: { size: content.length },
    }
  }

  const lines = content.trim().split(/\r?\n/)

  if (lines.length < 2) {
    return {
      success: false,
      error: 'CSV must have header and at least one data row',
      details: { lineCount: lines.length },
    }
  }

  const header = lines[0]
  // Split by comma, ignoring commas inside double quotes to count columns accurately
  const columnCount = header.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/).length

  if (columnCount < 7) {
    return {
      success: false,
      error: 'CSV must have at least 7 columns',
      details: { columnCount, minimumRequired: 7 },
    }
  }

  const warnings: string[] = []
  if (lines.length > 100_000) {
    warnings.push(`Large CSV: ${lines.length} rows`)
  }

  return {
    success: true,
    data: { lines, columnCount },
    warnings,
  }
}

export function validateNumber(value: unknown, fieldName: string): ValidationResult<number> {
  if (typeof value === 'number') {
    if (isNaN(value)) {
      return {
        success: false,
        error: `${fieldName} is NaN`,
        details: { value },
      }
    }
    if (!isFinite(value)) {
      return {
        success: false,
        error: `${fieldName} is not finite`,
        details: { value },
      }
    }
    return { success: true, data: value, warnings: [] }
  }

  if (typeof value === 'string') {
    const parsed = parseFloat(value)
    if (isNaN(parsed)) {
      return {
        success: false,
        error: `${fieldName} cannot be parsed as number`,
        details: { value, parsed },
      }
    }
    return { success: true, data: parsed, warnings: [] }
  }

  return {
    success: false,
    error: `${fieldName} must be a number or numeric string`,
    details: { valueType: typeof value, value },
  }
}
