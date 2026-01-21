import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard'

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
