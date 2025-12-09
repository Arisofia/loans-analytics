import Link from 'next/link';

export default function GrowthDashboard() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4 text-center">Growth Dashboard</h1>
      <p className="mb-6 text-gray-600 text-center">Origination, client retention, and channel performance KPIs. Click any card for full traceability and drill-down.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Origination Volume KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Origination Volume</h2>
          <p className="mb-2 text-gray-700">Total value of new loans originated this quarter</p>
          <div className="mb-2"><b>Latest:</b> $8.5M</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Growth</div>
          <Link href="/kpi/origination_volume" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Client Retention KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Client Retention</h2>
          <p className="mb-2 text-gray-700">Percentage of clients retained quarter-over-quarter</p>
          <div className="mb-2"><b>Latest:</b> 91%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Growth</div>
          <Link href="/kpi/client_retention" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Channel Performance KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Channel Performance</h2>
          <p className="mb-2 text-gray-700">Top performing acquisition channels</p>
          <div className="mb-2"><b>Latest:</b> Digital: 62%, Referral: 28%, Branch: 10%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Growth</div>
          <Link href="/kpi/channel_performance" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Add more KPI cards as needed */}
      </div>
      <div className="mt-8 text-sm text-gray-400 text-center">
        <span>Data last refreshed: 2025-12-08 09:00 UTC</span>
      </div>
    </div>
  );
}
