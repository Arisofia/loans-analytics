import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  reactCompiler: true,
  experimental: {
    turbopackUseSystemTlsCerts: true,
  },
  typescript: {
    tsconfigPath: './tsconfig.json',
  },
  experimental: {
    turbopackUseSystemTlsCerts: true,
  },
  turbopack: {
    root: __dirname,
  },
  // eslint-disable-next-line @typescript-eslint/require-await
  headers: async () => [
    {
      source: '/:path*',
      headers: [
        {
          key: 'X-Content-Type-Options',
          value: 'nosniff',
        },
        {
          key: 'X-Frame-Options',
          value: 'DENY',
        },
        {
          key: 'X-XSS-Protection',
          value: '1; mode=block',
        },
        {
          key: 'Referrer-Policy',
          value: 'strict-origin-when-cross-origin',
        },
      ],
    },
  ],
  // eslint-disable-next-line @typescript-eslint/require-await
  redirects: async () => [],
  // eslint-disable-next-line @typescript-eslint/require-await
  rewrites: async () => ({
    beforeFiles: [],
    afterFiles: [],
    fallback: [],
  }),
}

export default nextConfig
