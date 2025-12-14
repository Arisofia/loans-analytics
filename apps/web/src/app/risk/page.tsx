import Link from 'next/link'

const riskKpis = [
  {
    id: 'risk.par_90',
    title: 'Portfolio at Risk 90 (PAR90)',
    value: '3.2%',
    change: '-0.2 pp WoW',
    description: 'Balance 90+ days past due over total receivable.',
    provenance: 'kpi_snapshots → risk.par_90 (sql/models/risk/par_90.sql)',
    owner: 'Risk',
  },
  {
    id: 'risk.rdr_90',
    title: 'Roll-rate to Default (90d)',
    value: '6.8%',
    change: '+0.1 pp WoW',
    description: 'Cohort defaults past 90 days divided by starting balance.',
    provenance: 'kpi_snapshots → risk.rdr_90 (sql/models/risk/rdr_90.sql)',
    owner: 'Risk',
  },
  {
    id: 'risk.collection_rate',
    title: 'Collections Efficiency',
    value: '92.0%',
    change: '-0.3 pp d/d',
    description: 'Eligible receivables collected vs. total receivables.',
    provenance: 'kpi_snapshots → finance.collection_rate (sql/models/finance/collection_rate.sql)',
    owner: 'Collections',
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
}: (typeof riskKpis)[number]) {
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

export default function RiskDashboard() {
  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Risk Dashboard</h1>
        <p className="text-gray-600">
          Delinquency, roll-rate, and collections KPIs with provenance for CRO review.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {riskKpis.map((kpi) => (
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
