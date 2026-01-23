import { NextResponse } from 'next/server'
import { createFigmaKPIDashboard } from '@/lib/figmaKpiExport'

const BACKEND_KPI_URL = process.env.BACKEND_KPI_URL || 'http://127.0.0.1:8000/api/kpis/latest'

export async function GET() {
  try {
    const kpiResponse = await fetch(BACKEND_KPI_URL, {
      cache: 'no-store',
      headers: {
        'Accept': 'application/json',
      },
    })

    if (!kpiResponse.ok) {
      return NextResponse.json(
        {
          error: 'Failed to fetch KPI data from backend',
          status: kpiResponse.status,
        },
        { status: kpiResponse.status }
      )
    }

    const kpiRawData = await kpiResponse.json()
    const figmaDashboard = createFigmaKPIDashboard(kpiRawData)

    const hasDemoData =
      !kpiRawData.extended_kpis?.dpd_buckets ||
      (Array.isArray(kpiRawData.extended_kpis.dpd_buckets) && kpiRawData.extended_kpis.dpd_buckets.length === 0)

    figmaDashboard.metadata = {
      demo_mode: hasDemoData,
      total_kpis: figmaDashboard.total_metrics,
    }

    return NextResponse.json(figmaDashboard, {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=3600',
        'X-KPI-Version': '2.0',
        'X-Total-Metrics': String(figmaDashboard.total_metrics),
        'X-Demo-Mode': hasDemoData ? 'true' : 'false',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
      },
    })
  } catch (error) {
    console.error('Figma KPI Export Error:', error)
    return NextResponse.json(
      {
        error: 'Failed to generate KPI dashboard',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    )
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  })
}
