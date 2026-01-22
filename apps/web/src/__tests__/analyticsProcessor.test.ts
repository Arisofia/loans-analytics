import { parseLoanCsv, computeKPIs, toNumber } from '../lib/analyticsProcessor'

describe('toNumber', () => {
  it('should handle numeric input', () => {
    expect(toNumber(123.45)).toBe(123.45)
  })

  it('should handle simple string numeric input', () => {
    expect(toNumber('123.45')).toBe(123.45)
  })

  it('should handle currency symbols and commas', () => {
    expect(toNumber('$1,234.56')).toBe(1234.56)
  })

  it('should handle accounting format for negatives', () => {
    expect(toNumber('(1,234.56)')).toBe(-1234.56)
  })

  it('should return 0 for invalid input', () => {
    expect(toNumber('abc')).toBe(0)
  })
})

describe('parseLoanCsv', () => {
  it('should correctly parse a simple CSV string', () => {
    const csv = `loan_amount,appraised_value,borrower_income,monthly_debt,loan_status,interest_rate,principal_balance,dpd_status
100000,150000,60000,1000,current,5.5,95000,current
200000,250000,80000,2000,30-59 days past due,6.5,190000,bucket_30`

    const rows = parseLoanCsv(csv)
    expect(rows).toHaveLength(2)
    expect(rows[0].loan_amount).toBe(100000)
    expect(rows[0].loan_status).toBe('current')
    expect(rows[1].loan_amount).toBe(200000)
    expect(rows[1].loan_status).toBe('30-59 days past due')
  })

  it('should handle quoted values with commas', () => {
    const csv = `loan_amount,appraised_value,borrower_income,monthly_debt,loan_status,interest_rate,principal_balance,dpd_status
"100,000",150000,60000,1000,"current, with note",5.5,95000,current`

    const rows = parseLoanCsv(csv)
    expect(rows).toHaveLength(1)
    expect(rows[0].loan_amount).toBe(100000)
    expect(rows[0].loan_status).toBe('current, with note')
  })

  it('should handle currency symbols and accounting format', () => {
    const csv = `loan_amount,appraised_value,borrower_income,monthly_debt,loan_status,interest_rate,principal_balance,dpd_status
"$100,000.00",150000,60000,1000,current,5.5,95000,current
"(50,000)",100000,40000,500,delinquent,4.0,45000,bucket_30`

    const rows = parseLoanCsv(csv)
    expect(rows[0].loan_amount).toBe(100000)
    expect(rows[1].loan_amount).toBe(-50000)
  })
})

describe('computeKPIs', () => {
  it('should calculate KPIs correctly', () => {
    const rows = [
      {
        loan_amount: 100000,
        appraised_value: 200000,
        borrower_income: 120000,
        monthly_debt: 2000,
        loan_status: 'current',
        interest_rate: 5,
        principal_balance: 100000,
        dpd_status: 'current',
      },
      {
        loan_amount: 100000,
        appraised_value: 200000,
        borrower_income: 120000,
        monthly_debt: 2000,
        loan_status: '30-59 days past due',
        interest_rate: 10,
        principal_balance: 100000,
        dpd_status: 'bucket_30',
      },
    ]

    const kpis = computeKPIs(rows)
    expect(kpis.loanCount).toBe(2)
    expect(kpis.delinquencyRate).toBe(50) // 1 out of 2
    expect(kpis.portfolioYield).toBe(7.5) // (5*100k + 10*100k) / 200k
    expect(kpis.averageLTV).toBe(50) // (100k/200k + 100k/200k) / 2 * 100
    expect(kpis.averageDTI).toBe(20) // (2000 / (120000/12)) * 100 = 20%
  })
})
