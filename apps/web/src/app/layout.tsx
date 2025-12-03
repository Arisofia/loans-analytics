import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
