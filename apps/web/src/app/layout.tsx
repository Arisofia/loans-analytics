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
>>>>>>> main
    </html>
  )
}
