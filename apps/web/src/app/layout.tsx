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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
<<<<<<< HEAD
    <html lang="en">
      <body className={inter.className}>{children}</body>
=======
    <html lang="en" className={inter.className}>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
>>>>>>> origin/main
    </html>
  )
}
