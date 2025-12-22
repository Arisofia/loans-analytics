import Link from 'next/link'

const boardKpis = [
  {
    id: 'finance.arr',
    title: 'Annual Recurring Revenue (ARR)',
    value: '$2.1M',
    change: '+4.5% MoM',
    description: 'Total recurring revenue from all active clients.',
    provenance: 'kpi_snapshots → finance.arr (sql/models/finance/arr.sql)',
    owner: 'Finance',
  },
  {
    id: 'growth.origination_volume',
    title: 'Origination Volume',
    value: '$8.5M',
    change: '+12.0% QoQ',
    description: 'Value of loans funded this quarter.',
    provenance: 'kpi_snapshots → growth.origination_volume (sql/models/growth/originations.sql)',
    owner: 'Growth',
  },
  {
    id: 'risk.par_90',
    title: 'Portfolio at Risk 90 (PAR90)',
    value: '3.2%',
    change: '-0.2 pp WoW',
    description: 'Outstanding balance 90+ days past due.',
    provenance: 'kpi_snapshots → risk.par_90 (sql/models/risk/par_90.sql)',
    owner: 'Risk',
  },
]

function PersonaCard({
  title,
  value,
  change,
  description,
  provenance,
  owner,
  id,
}: (typeof boardKpis)[number]) {
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
  )
}

export default function BoardDashboard() {
  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Board Dashboard</h1>
        <p className="text-gray-600">
          Strategic overview of finance, growth, and risk KPIs with provenance tooltips and
          drill-down access.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {boardKpis.map((kpi) => (
          <PersonaCard key={kpi.id} {...kpi} />
        ))}
      </div>
      <div className="mt-4 text-sm text-gray-400 text-center">
        Data last refreshed: 2025-01-15 07:00 UTC · Source: Cascade exports · Contracted via
        config/personas.yml
      </div>
    </div>
  )
}
