import { type NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(request: NextRequest) {
  const supabase = createClient()
  // @ts-expect-error - Mock client types are incomplete
  await supabase.auth.signOut()
  return NextResponse.redirect(new URL('/', request.url), {
    status: 302,
  })
}
