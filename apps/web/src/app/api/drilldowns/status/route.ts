import { NextResponse } from 'next/server'

const DEFAULT_STATUSES: Record<string, 'ok' | 'error'> = {
  '/delinquency': 'ok',
  '/roll-rate': 'ok',
  '/collections': 'ok',
  '/ingestion-errors': 'ok',
}

export function GET() {
  return NextResponse.json(DEFAULT_STATUSES)
}
