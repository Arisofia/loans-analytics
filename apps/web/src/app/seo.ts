import type { Metadata } from 'next'

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://abaco-loans-analytics.com'

const sharedDescription =
  'Abaco Loans Analytics unifies lending KPIs, governance, and revenue acceleration in one compliant, investor-ready experience.'

export const siteMetadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: 'Abaco Loans Analytics | Growth & Risk Intelligence',
  description: sharedDescription,
  applicationName: 'Abaco Loans Analytics',
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
    title: 'Abaco Loans Analytics | Growth & Risk Intelligence',
    description: sharedDescription,
    type: 'website',
    siteName: 'Abaco Loans Analytics',
    locale: 'en_US',
    images: [
      {
        url: '/window.svg',
        width: 1200,
        height: 630,
        alt: 'Abaco Loans Analytics dashboard previews',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Abaco Loans Analytics | Growth & Risk Intelligence',
    description: sharedDescription,
    images: ['/window.svg'],
  },
  robots: {
    index: true,
    follow: true,
  },
  authors: [{ name: 'Abaco Growth & Risk Intelligence' }],
  creator: 'Abaco Growth & Risk Intelligence',
  publisher: 'Abaco Loans Analytics',
}
