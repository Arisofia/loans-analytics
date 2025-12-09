import Link from 'next/link';

export default function BoardDashboard() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4 text-center">Board Dashboard</h1>
      <p className="mb-6 text-gray-600 text-center">Strategic overview of key financial, growth, and risk KPIs. Click any card for full traceability and drill-down.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* PAR90 KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Portfolio at Risk 90 (PAR90)</h2>
          <p className="mb-2 text-gray-700">Outstanding balance 90+ days past due</p>
          <div className="mb-2"><b>Latest:</b> 3.2%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Risk Ops</div>
          <Link href="/kpi/par_90" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* ARR KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Annual Recurring Revenue (ARR)</h2>
          <p className="mb-2 text-gray-700">Total recurring revenue from all active clients</p>
          <div className="mb-2"><b>Latest:</b> $2.1M</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Finance</div>
          <Link href="/kpi/arr" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Origination Volume KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Origination Volume</h2>
          <p className="mb-2 text-gray-700">Total value of new loans originated this quarter</p>
          <div className="mb-2"><b>Latest:</b> $8.5M</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Growth</div>
          <Link href="/kpi/origination_volume" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Client Retention KPI (Growth) */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Client Retention</h2>
          <p className="mb-2 text-gray-700">Percentage of clients retained quarter-over-quarter</p>
          <div className="mb-2"><b>Latest:</b> 91%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Growth</div>
          <Link href="/kpi/client_retention" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Sales Conversion Rate KPI (Sales) */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Sales Conversion Rate</h2>
          <p className="mb-2 text-gray-700">Ratio of closed deals to total leads</p>
          <div className="mb-2"><b>Latest:</b> 27%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Sales</div>
          <Link href="/kpi/sales_conversion" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Marketing Campaign ROI KPI (Marketing) */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Marketing Campaign ROI</h2>
          <p className="mb-2 text-gray-700">Return on investment for latest marketing campaign</p>
          <div className="mb-2"><b>Latest:</b> 4.2x</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Marketing</div>
          <Link href="/kpi/marketing_roi" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* System Uptime KPI (Tech) */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">System Uptime</h2>
          <p className="mb-2 text-gray-700">Percentage of time platform is available</p>
          <div className="mb-2"><b>Latest:</b> 99.98%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Tech</div>
          <Link href="/kpi/system_uptime" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Compliance Audit Flags KPI (Risk/Compliance) */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Compliance Audit Flags</h2>
          <p className="mb-2 text-gray-700">Number of open compliance issues flagged in last audit</p>
          <div className="mb-2"><b>Latest:</b> 2</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Compliance</div>
          <Link href="/kpi/compliance_flags" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Investor Yield KPI (Investors) */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Investor Yield</h2>
          <p className="mb-2 text-gray-700">Average yield delivered to investors YTD</p>
          <div className="mb-2"><b>Latest:</b> 7.8%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Investors</div>
          <Link href="/kpi/investor_yield" className="text-blue-600 hover:underline">View Details</Link>
        </div>
      </div>
      <div className="mt-8 text-sm text-gray-400 text-center">
        <span>Data last refreshed: 2025-12-08 09:00 UTC</span>
      </div>
    </div>
  );
}
