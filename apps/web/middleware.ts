import { createServerClient } from '@supabase/ssr'
import { type NextRequest, NextResponse } from 'next/server'

export async function middleware(request: NextRequest) {
  const allowE2EBypass =
    process.env.E2E_BYPASS_AUTH === '1' &&
    (process.env.CI === 'true' || process.env.NODE_ENV !== 'production')

  if (allowE2EBypass) {
    return NextResponse.next()
  }

  // Mitigation for CVE-2025-29927: block requests that contain
  // `x-middleware-subrequest` unless an internal shared secret is present.
  // This provides defense-in-depth in addition to any infra/WAF rules.
  const subreq = request.headers.get('x-middleware-subrequest')
  if (subreq) {
    const shared = request.headers.get('x-internal-shared-secret')
    if (shared !== process.env.MIDDLEWARE_SHARED_SECRET) {
      console.warn('Blocked middleware subrequest spoofing attempt')
      return new Response('Forbidden', { status: 403 })
    }
  }

  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Supabase environment variables are missing')
    return response
  }

  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll()
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value, options: _options }) =>
          request.cookies.set(name, value)
        )
        response = NextResponse.next({
          request: {
            headers: request.headers,
          },
        })
        cookiesToSet.forEach(({ name, value, options: _options }) =>
          response.cookies.set(name, value, _options)
        )
      },
    },
  })

  // Refresh session if expired - required for Server Components
  await supabase.auth.getUser()

  return response
}
