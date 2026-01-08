import { type NextRequest } from 'next/server'
import { middleware } from '../middleware'

describe('middleware header spoofing mitigation', () => {
  test('blocks x-middleware-subrequest without shared secret', async () => {
    const req = {
      headers: {
        get: (k: string) => (k === 'x-middleware-subrequest' ? '1' : null),
      },
      cookies: { getAll: () => [] },
    } as unknown as NextRequest

    const res = (await middleware(req)) as unknown as Response
    expect(res?.status).toBe(403)
  })

  test('allows when internal shared secret matches', async () => {
    process.env.MIDDLEWARE_SHARED_SECRET = 'test-secret'
    const headers = new Headers()
    headers.set('x-middleware-subrequest', '1')
    headers.set('x-internal-shared-secret', 'test-secret')

    const req = {
      headers,
      cookies: { getAll: () => [] },
    } as unknown as NextRequest

    const res = (await middleware(req)) as unknown as Response
    expect(res?.status === 403).toBeFalsy()
  })
})
