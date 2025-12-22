import type { ReactNode } from 'react'

export const metadata = {
  title: 'Abaco Loans Analytics',
  description: 'Analytics experience for Abaco Loans',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
