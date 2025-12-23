import Link from 'next/link'

export default function SalesDashboard() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4 text-center">Sales Dashboard</h1>
      <p className="mb-6 text-gray-600 text-center">
        Sales pipeline, conversion, and revenue KPIs. Click any card for full traceability and
        drill-down.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Sales Conversion Rate KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Sales Conversion Rate</h2>
          <p className="mb-2 text-gray-700">Ratio of closed deals to total leads</p>
          <div className="mb-2">
            <b>Latest:</b> 27%
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Sales</div>
          <Link href="/kpi/sales_conversion" className="text-blue-600 hover:underline">
            View Details
          </Link>
        </div>
        {/* Pipeline Value KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Pipeline Value</h2>
          <p className="mb-2 text-gray-700">Total value of open opportunities</p>
          <div className="mb-2">
            <b>Latest:</b> $3.4M
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Sales</div>
          <Link href="/kpi/pipeline_value" className="text-blue-600 hover:underline">
            View Details
          </Link>
        </div>
        {/* Win Rate KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Win Rate</h2>
          <p className="mb-2 text-gray-700">Percentage of opportunities won</p>
          <div className="mb-2">
            <b>Latest:</b> 34%
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Sales</div>
          <Link href="/kpi/win_rate" className="text-blue-600 hover:underline">
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
