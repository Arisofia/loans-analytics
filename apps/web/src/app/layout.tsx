import type { ReactNode } from 'react'
import type { Metadata } from 'next'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import { Inter } from 'next/font/google'

import './globals.css'
import { siteMetadata } from './seo'
import { SkipLink } from './skip-link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = siteMetadata

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        <SkipLink />
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
