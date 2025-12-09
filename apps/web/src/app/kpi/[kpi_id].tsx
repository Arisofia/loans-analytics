import { FC } from 'react';
import { useParams } from 'next/navigation';

// Mock KPI data (replace with API/backend integration later)
const kpiCatalog: Record<string, KPI> = {
  'par_90': {
    name: 'Portfolio at Risk 90 (PAR90)',
    description: 'Outstanding balance 90+ days past due',
    formula: 'SUM(balance_90plus) / SUM(total_balance)',
    thresholds: { warning: '3%', critical: '5%' },
    owner: 'Risk Ops',
    source: 'kpi_definitions.yaml',
    sql: 'par_90_calculation.sql',
    lastRefresh: '2025-12-08T09:00:00Z',
    version: 'v1.2',
    dataTimestamp: '2025-12-08T08:55:00Z',
    segmentBreakdown: [
      { segment: 'Consumer', value: 2.8 },
      { segment: 'SME', value: 3.5 },
      { segment: 'Corporate', value: 1.9 }
    ]
  },
  // Add more KPIs as needed
};

interface KPI {
  name: string;
  description: string;
  formula: string;
  thresholds: { warning: string; critical: string };
  owner: string;
  source: string;
  sql: string;
  lastRefresh: string;
  version: string;
  dataTimestamp: string;
  segmentBreakdown: Array<{ segment: string; value: number }>;
}

const ProvenanceTooltip: FC<{ kpi: KPI }> = ({ kpi }) => (
  <div className="text-xs text-gray-500 mt-2">
    <span className="mr-2">Data timestamp: {kpi.dataTimestamp}</span>
    <span className="mr-2">Source: <a href={`https://github.com/Abaco-Technol/abaco-loans-analytics/blob/main/config/kpis/${kpi.source}`} target="_blank" rel="noopener noreferrer">{kpi.source}</a></span>
    <span className="mr-2">SQL: <a href={`https://github.com/Abaco-Technol/abaco-loans-analytics/blob/main/sql/calculations/${kpi.sql}`} target="_blank" rel="noopener noreferrer">{kpi.sql}</a></span>
    <span>Version: {kpi.version}</span>
  </div>
);

const KPIDrilldownPage: FC = () => {
  const params = useParams();
  const kpiId = typeof params === 'object' && params !== null ? (params['kpi_id'] as string) : 'par_90';
  const kpi = kpiCatalog[kpiId] || kpiCatalog['par_90'];

  if (!kpi) {
    return <div className="p-8">KPI not found.</div>;
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-2">{kpi.name}</h1>
      <div className="mb-2 text-gray-700">{kpi.description}</div>
      <div className="mb-2"><b>Formula:</b> <span className="font-mono bg-gray-100 px-2 py-1 rounded">{kpi.formula}</span></div>
      <div className="mb-2"><b>Thresholds:</b> <span className="text-yellow-600">Warning: {kpi.thresholds.warning}</span>, <span className="text-red-600">Critical: {kpi.thresholds.critical}</span></div>
      <div className="mb-2"><b>Owner:</b> {kpi.owner}</div>
      <div className="mb-2"><b>Last Refresh:</b> {kpi.lastRefresh}</div>
      <ProvenanceTooltip kpi={kpi} />
      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-2">Segment Breakdown</h2>
        <table className="min-w-full border text-sm">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-2 py-1 border">Segment</th>
              <th className="px-2 py-1 border">Value (%)</th>
            </tr>
          </thead>
          <tbody>
            {kpi.segmentBreakdown.map((row, idx) => (
              <tr key={idx}>
                <td className="px-2 py-1 border">{row.segment}</td>
                <td className="px-2 py-1 border">{row.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default KPIDrilldownPage;
