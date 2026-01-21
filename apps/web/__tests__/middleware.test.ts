import { middleware } from '../middleware'

describe('middleware header spoofing mitigation', () => {
  interface MockRequest {
    headers: {
      get: (k: string) => string | null
    } | Headers
    cookies: { getAll: () => any[] }
  }

  interface MockResponse {
    status?: number
  }

  test('blocks x-middleware-subrequest without shared secret', async () => {
    const req: MockRequest = {
      headers: {
        get: (k: string) => (k === 'x-middleware-subrequest' ? '1' : null),
      },
      cookies: { getAll: () => [] },
    }

    const res = await middleware(req as any) as MockResponse
    expect(res?.status).toBe(403)
  })

  test('allows when internal shared secret matches', async () => {
    process.env.MIDDLEWARE_SHARED_SECRET = 'test-secret'
    const headers = new Headers()
    headers.set('x-middleware-subrequest', '1')
    headers.set('x-internal-shared-secret', 'test-secret')

    const req: MockRequest = {
      headers,
      cookies: { getAll: () => [] },
    }

    const res = await middleware(req as any) as MockResponse
    expect(res?.status === 403).toBeFalsy()
  })
})
