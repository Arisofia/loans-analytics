import { NextResponse } from 'next/server'

export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_DRILLDOWN_BASE_URL || 'http://127.0.0.1:8000'
  try {
    const res = await fetch(`${backendUrl}/api/kpis/latest`, {
      cache: 'no-store'
    })
    if (!res.ok) {
      return NextResponse.json({ error: 'Backend error' }, { status: res.status })
    }
    const data = await res.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Proxy error:', error)
    return NextResponse.json({ error: 'Proxy failed' }, { status: 500 })
  }
}
