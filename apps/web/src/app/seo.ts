import type { Metadata } from 'next'

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://abaco-loans-analytics.com'

const sharedDescription =
  'ABACO — Loan Intelligence delivers growth-ready analytics for credit, collections, finance, and funding teams with audit-ready controls.'

export const siteMetadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: 'ABACO — Loan Intelligence',
  description: sharedDescription,
  applicationName: 'ABACO — Loan Intelligence',
  keywords: [
    'lending analytics',
    'fintech dashboards',
    'risk intelligence',
    'credit decisioning',
    'compliance automation',
    'treasury governance',
    'portfolio monitoring',
    'loan servicing',
    'portfolio governance',
  ],
  alternates: {
    canonical: '/',
  },
  openGraph: {
    url: siteUrl,
    title: 'ABACO — Loan Intelligence',
    description: sharedDescription,
    type: 'website',
    siteName: 'ABACO — Loan Intelligence',
    locale: 'en_US',
    images: [
      {
        url: '/window.svg',
        width: 1200,
        height: 630,
        alt: 'ABACO Loan Intelligence dashboard previews',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ABACO — Loan Intelligence',
    description: sharedDescription,
    images: ['/window.svg'],
  },
  robots: {
    index: true,
    follow: true,
  },
  authors: [{ name: 'ABACO Loan Intelligence' }],
  creator: 'ABACO Loan Intelligence',
  publisher: 'ABACO Loan Intelligence',
}
