import Link from 'next/link';

const cfoKpis = [
  {
    id: 'finance.cash_position',
    title: 'Cash Position',
    value: '$4.7M',
    change: '+$250k d/d',
    description: 'Available operating cash after restricted balances.',
    provenance: 'kpi_snapshots → finance.cash_position (sql/models/finance/cash_position.sql)',
    owner: 'Treasury'
  },
  {
    id: 'finance.collection_rate',
    title: 'Collection Rate',
    value: '92.0%',
    change: '-0.3 pp d/d',
    description: 'Eligible receivables collected over total receivables.',
    provenance: 'kpi_snapshots → finance.collection_rate (sql/models/finance/collection_rate.sql)',
    owner: 'Collections'
  },
  {
    id: 'finance.write_off_rate',
    title: 'Write-off Rate',
    value: '1.4%',
    change: '+0.05 pp m/m',
    description: 'Charge-offs divided by average principal outstanding.',
    provenance: 'kpi_snapshots → finance.write_off_rate (sql/models/finance/write_off_rate.sql)',
    owner: 'Finance'
  }
];

function PersonaCard({
  title,
  value,
  change,
  description,
  provenance,
  owner,
  id
}: (typeof cfoKpis)[number]) {
  return (
    <div className="border rounded p-4 bg-white shadow hover:shadow-lg transition" data-kpi-id={id}>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold mb-1">{title}</h2>
          <p className="mb-2 text-gray-700">{description}</p>
        </div>
        <span className="text-xs text-gray-500 ml-2" title={`Provenance: ${provenance}`}>
          ℹ️
        </span>
      </div>
      <div className="mb-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold">{value}</span>
        <span className="text-sm text-green-600">{change}</span>
      </div>
      <div className="mb-2 text-xs text-gray-500">Owner: {owner}</div>
      <Link href={`/kpi/${id}`} className="text-blue-600 hover:underline text-sm">
        View details & lineage
      </Link>
    </div>
  );
}

export default function CFODashboard() {
  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">CFO Dashboard</h1>
        <p className="text-gray-600">
          Liquidity, collections, and ARR safeguards with persona contracts and provenance tooltips.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cfoKpis.map((kpi) => (
          <PersonaCard key={kpi.id} {...kpi} />
        ))}
      </div>
      <div className="mt-4 text-sm text-gray-400 text-center">
        Data last refreshed: 2025-01-15 07:00 UTC · Source: Cascade exports · Contracted via config/personas.yml
      </div>
    </div>
  );
}
