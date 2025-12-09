import Link from 'next/link';

export default function InvestorsDashboard() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4 text-center">Investors Dashboard</h1>
      <p className="mb-6 text-gray-600 text-center">Yield, AUM, and portfolio performance KPIs. Click any card for full traceability and drill-down.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Investor Yield KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Investor Yield</h2>
          <p className="mb-2 text-gray-700">Average yield delivered to investors YTD</p>
          <div className="mb-2"><b>Latest:</b> 7.8%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Investors</div>
          <Link href="/kpi/investor_yield" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Assets Under Management KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Assets Under Management (AUM)</h2>
          <p className="mb-2 text-gray-700">Total value of assets managed</p>
          <div className="mb-2"><b>Latest:</b> $120M</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Investors</div>
          <Link href="/kpi/aum" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Portfolio Performance KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Portfolio Performance</h2>
          <p className="mb-2 text-gray-700">Quarterly return vs. benchmark</p>
          <div className="mb-2"><b>Latest:</b> +1.2% vs. benchmark</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Investors</div>
          <Link href="/kpi/portfolio_performance" className="text-blue-600 hover:underline">View Details</Link>
        </div>
      </div>
      <div className="mt-8 text-sm text-gray-400 text-center">
        <span>Data last refreshed: 2025-12-08 09:00 UTC</span>
      </div>
    </div>
  );
}
