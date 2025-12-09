import Link from 'next/link';

const growthKpis = [
  {
    id: 'growth.origination_volume',
    title: 'Origination Volume',
    value: '$8.5M',
    change: '+12.0% QoQ',
    description: 'Value of funded loans across all channels.',
    provenance: 'kpi_snapshots → growth.origination_volume (sql/models/growth/originations.sql)',
    owner: 'Growth'
  },
  {
    id: 'growth.client_retention',
    title: 'Client Retention',
    value: '91%',
    change: '+0.8 pp QoQ',
    description: 'Percentage of clients retained quarter-over-quarter.',
    provenance: 'kpi_snapshots → growth.client_retention (sql/models/growth/client_retention.sql)',
    owner: 'Growth'
  },
  {
    id: 'growth.channel_efficiency',
    title: 'Channel CAC-to-LTV',
    value: '3.8x',
    change: '+0.2x QoQ',
    description: 'Channel-level LTV divided by CAC.',
    provenance: 'kpi_snapshots → growth.channel_efficiency (sql/models/growth/channel_efficiency.sql)',
    owner: 'Marketing'
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
}: (typeof growthKpis)[number]) {
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

export default function GrowthDashboard() {
  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Growth Dashboard</h1>
        <p className="text-gray-600">
          Acquisition, retention, and pipeline conversion KPIs with contract-aware provenance.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {growthKpis.map((kpi) => (
          <PersonaCard key={kpi.id} {...kpi} />
        ))}
      </div>
      <div className="mt-4 text-sm text-gray-400 text-center">
        Data last refreshed: 2025-01-15 07:00 UTC · Source: Cascade exports · Contracted via config/personas.yml
      </div>
    </div>
  );
}
