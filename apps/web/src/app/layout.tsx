import type { ReactNode } from 'react'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import { Inter } from 'next/font/google'
import './globals.css'
import { siteMetadata } from './seo'

const inter = Inter({ subsets: ['latin'] })

export const metadata = siteMetadata

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode
}>) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        <a className="skipLink" href="#main-content">
          Skip to main content
        </a>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
