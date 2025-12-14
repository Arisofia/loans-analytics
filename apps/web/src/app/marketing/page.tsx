import Link from 'next/link'

export default function MarketingDashboard() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4 text-center">Marketing Dashboard</h1>
      <p className="mb-6 text-gray-600 text-center">
        Campaign ROI, lead generation, and engagement KPIs. Click any card for full traceability and
        drill-down.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Campaign ROI KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Campaign ROI</h2>
          <p className="mb-2 text-gray-700">Return on investment for latest marketing campaign</p>
          <div className="mb-2">
            <b>Latest:</b> 4.2x
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Marketing</div>
          <Link href="/kpi/marketing_roi" className="text-blue-600 hover:underline">
            View Details
          </Link>
        </div>
        {/* Lead Generation KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Lead Generation</h2>
          <p className="mb-2 text-gray-700">Number of new leads generated this month</p>
          <div className="mb-2">
            <b>Latest:</b> 1,250
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Marketing</div>
          <Link href="/kpi/lead_generation" className="text-blue-600 hover:underline">
            View Details
          </Link>
        </div>
        {/* Engagement Rate KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Engagement Rate</h2>
          <p className="mb-2 text-gray-700">Percentage of engaged contacts</p>
          <div className="mb-2">
            <b>Latest:</b> 38%
          </div>
          <div className="mb-2 text-xs text-gray-500">Owner: Marketing</div>
          <Link href="/kpi/engagement_rate" className="text-blue-600 hover:underline">
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
