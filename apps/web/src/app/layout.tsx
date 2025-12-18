<<<<<<< HEAD
import type { Metadata } from 'next'
=======
import type { ReactNode } from 'react'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import { Inter } from 'next/font/google'
>>>>>>> main
import './globals.css'
import { siteMetadata } from './seo'

<<<<<<< HEAD
export const metadata: Metadata = {
  title: 'ABACO Loan Analytics',
  description: 'Executive-grade lending intelligence and governance.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
=======
const inter = Inter({ subsets: ['latin'] })

<<<<<<< HEAD
export const metadata: Metadata = {
  title: 'Abaco Loans Analytics',
  description: 'Customer-centric lending intelligence with governed growth for Abaco clients.',
<<<<<<< HEAD
  keywords: ['lending', 'risk management', 'fintech analytics', 'governance', 'customer growth'],
  openGraph: {
    title: 'Abaco Loans Analytics',
    description:
      'Customer-centric lending intelligence with governed growth for Abaco clients and partners.',
    url: 'https://abaco-loans-analytics.example.com',
    siteName: 'Abaco Loans Analytics',
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Abaco Loans Analytics',
    description:
      'Audit-ready underwriting, portfolio visibility, and growth acceleration for lenders.',
  },
=======
>>>>>>> origin/main
}
=======
export const metadata = siteMetadata
>>>>>>> origin/main

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
>>>>>>> main
    </html>
  )
}
