import Link from 'next/link'

export default function TechDashboard() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4 text-center">Tech Dashboard</h1>
      <p className="mb-6 text-gray-600 text-center">
        System uptime, deployment, and incident KPIs. Click any card for full traceability and
        drill-down.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* System Uptime KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">System Uptime</h2>
          <p className="mb-2 text-gray-700">Percentage of time platform is available</p>
          <div className="mb-2">
            <b>Latest:</b> 99.98%
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Tech</div>
          <Link href="/kpi/system_uptime" className="text-blue-600 hover:underline">
            View Details
          </Link>
        </div>
        {/* Deployment Frequency KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Deployment Frequency</h2>
          <p className="mb-2 text-gray-700">Number of production deployments this month</p>
          <div className="mb-2">
            <b>Latest:</b> 14
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Tech</div>
          <Link href="/kpi/deployment_frequency" className="text-blue-600 hover:underline">
            View Details
          </Link>
        </div>
        {/* Incident MTTR KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Incident MTTR</h2>
          <p className="mb-2 text-gray-700">Mean time to recovery for incidents</p>
          <div className="mb-2">
            <b>Latest:</b> 42 min
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Tech</div>
          <Link href="/kpi/incident_mttr" className="text-blue-600 hover:underline">
            View Details
          </Link>
        </div>
      </div>
      <div className="mt-8 text-sm text-gray-400 text-center">
        <span>Data last refreshed: 2025-12-08 09:00 UTC</span>
      </div>
    </div>
  )
}
