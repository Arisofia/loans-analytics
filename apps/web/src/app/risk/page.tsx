import Link from 'next/link';

export default function RiskDashboard() {
  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-4 text-center">Risk Dashboard</h1>
      <p className="mb-6 text-gray-600 text-center">Portfolio health, delinquency, and scenario risk KPIs. Click any card for full traceability and drill-down.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* PAR90 KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Portfolio at Risk 90 (PAR90)</h2>
          <p className="mb-2 text-gray-700">Outstanding balance 90+ days past due</p>
          <div className="mb-2"><b>Latest:</b> 3.2%</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Risk Ops</div>
          <Link href="/kpi/par_90" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Portfolio Health KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Portfolio Health</h2>
          <p className="mb-2 text-gray-700">Composite score of loan book quality</p>
          <div className="mb-2"><b>Latest:</b> 87</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Risk</div>
          <Link href="/kpi/portfolio_health" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Loss Scenarios KPI */}
        <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition">
          <h2 className="text-lg font-semibold mb-2">Loss Scenarios</h2>
          <p className="mb-2 text-gray-700">Projected loss under stress scenarios</p>
          <div className="mb-2"><b>Latest:</b> $1.2M</div>
          <div className="mb-2 text-xs text-gray-500">Owner: Risk</div>
          <Link href="/kpi/loss_scenarios" className="text-blue-600 hover:underline">View Details</Link>
        </div>
        {/* Add more KPI cards as needed */}
      </div>
      <div className="mt-8 text-sm text-gray-400 text-center">
        <span>Data last refreshed: 2025-12-08 09:00 UTC</span>
      </div>
    </div>
  );
}
