import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ABACO Loan Analytics',
  description: 'Executive-grade lending intelligence and governance.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
