<<<<<<< HEAD
import './globals.css'

import { siteMetadata } from './seo'

export const metadata = siteMetadata
=======
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
<<<<<<< HEAD
=======
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'
>>>>>>> origin/main
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Abaco Loans Analytics',
  description: 'Customer-centric lending intelligence with governed growth for Abaco clients.',
}
>>>>>>> origin/main

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
<<<<<<< HEAD
    <html lang="en">
<<<<<<< HEAD
      <body>
        <a className="skipLink" href="#main-content">
          Skip to main content
        </a>
        {children}
=======
      <body className={inter.className}>{children}</body>
>>>>>>> upstream/main
=======
    <html lang="en" className={inter.className}>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
>>>>>>> origin/main
      </body>
>>>>>>> origin/main
    </html>
  )
}
