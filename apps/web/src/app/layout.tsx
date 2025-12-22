import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import './globals.css'
import { SkipLink } from './skip-link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ABACO — Loan Intelligence',
  description: 'Growth-ready analytics for credit, collections, finance, and funding teams.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
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
