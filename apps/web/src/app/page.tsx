import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard'
import { type AnalyticsData, type Metric } from '@/types/analytics'

// Define local interfaces if not imported
interface Product {
  id: string;
  name: string;
}

interface Step {
  name: string;
  status: 'complete' | 'current' | 'upcoming';
}

const fallbackData: AnalyticsData = {
  period: 'Q4 2023',
  metrics: [
    { id: 'vol', label: 'Total Volume', value: 2500000, trend: 'up', change: 12 },
    { id: 'active', label: 'Active Loans', value: 145, trend: 'up', change: 5 },
    { id: 'default', label: 'Default Rate', value: 2.4, trend: 'down', change: -0.5 },
  ]
}

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-8">Abaco Loans Analytics</h1>
      </div>
      
      <div className="w-full max-w-5xl">
        <AnalyticsDashboard />
      </div>
    </main>
  )
}
