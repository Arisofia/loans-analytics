import Link from 'next/link';

export default function CFODashboard() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4 text-center">CFO Dashboard</h1>
      <p className="mb-6 text-gray-600 text-center">Financial health, cash position, and collections KPIs. Click any card for full traceability and drill-down.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* ARR KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Annual Recurring Revenue (ARR)</h2>
          <p className="mb-2 text-gray-700">Total recurring revenue from all active clients</p>
          <div className="mb-2"><b>Latest:</b> $2.1M</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Finance</div>
          <Link href="/kpi/arr" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Write-Off Rate KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Write-Off Rate</h2>
          <p className="mb-2 text-gray-700">Percentage of loans written off YTD</p>
          <div className="mb-2"><b>Latest:</b> 1.4%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Finance</div>
          <Link href="/kpi/write_off_rate" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Collection Rate KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Collection Rate</h2>
          <p className="mb-2 text-gray-700">Percentage of due payments collected</p>
          <div className="mb-2"><b>Latest:</b> 97.2%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Finance</div>
          <Link href="/kpi/collection_rate" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Cash Position KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Cash Position</h2>
          <p className="mb-2 text-gray-700">Current available cash for operations</p>
          <div className="mb-2"><b>Latest:</b> $4.7M</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Finance</div>
          <Link href="/kpi/cash_position" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Add more KPI cards as needed */}
      </div>
      <div className="mt-8 text-sm text-gray-400 text-center">
        <span>Data last refreshed: 2025-12-08 09:00 UTC</span>
      </div>
    </div>
  );
}
