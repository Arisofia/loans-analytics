import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { MultiLineChart } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Button } from "@/components/ui/button";
import { Users, AlertTriangle, DollarSign, Phone } from "lucide-react";

interface CollectionsData {
  metrics: {
    collection_rate: number;
    dpd_over_30: number;
    collections_mtd: number;
    contact_rate: number;
  };
  dpd_distribution: Array<{
    bucket: string;
    count: number;
    amount: number;
    percentage: number;
  }>;
  collections_trend: Array<{
    month: string;
    collected: number;
    target: number;
  }>;
}

export default function CollectionsOperations() {
  const { data, loading, error, refetch } = useSection<CollectionsData>("collections");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { metrics, dpd_distribution, collections_trend } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Collections Operations
          </h1>
          <p style={{ color: 'var(--medium-gray)' }}>
            Collection performance and delinquency management
          </p>
        </div>
        <Button size="sm" className="gap-2">
          <Users className="h-4 w-4" />
          Run Multi-Agent Analysis
        </Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Collection Rate"
          value={`${metrics.collection_rate.toFixed(1)}%`}
          icon={DollarSign}
          status={metrics.collection_rate >= 95 ? "good" : metrics.collection_rate >= 85 ? "warning" : "critical"}
        />
        <MetricCard
          title="DPD > 30"
          value={metrics.dpd_over_30.toLocaleString()}
          icon={AlertTriangle}
          status={metrics.dpd_over_30 > 100 ? "critical" : metrics.dpd_over_30 > 50 ? "warning" : "good"}
        />
        <MetricCard
          title="Collections MTD"
          value={`$${(metrics.collections_mtd / 1e3).toFixed(0)}K`}
          icon={DollarSign}
          status="neutral"
        />
        <MetricCard
          title="Contact Rate"
          value={`${metrics.contact_rate.toFixed(1)}%`}
          icon={Phone}
          status={metrics.contact_rate >= 80 ? "good" : metrics.contact_rate >= 60 ? "warning" : "critical"}
        />
      </div>

      {/* DPD Distribution Table */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          DPD Distribution
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Bucket</th>
                <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Count</th>
                <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Amount</th>
                <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>%</th>
                <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Distribution</th>
              </tr>
            </thead>
            <tbody>
              {dpd_distribution.map((row) => (
                <tr key={row.bucket} style={{ borderBottom: '1px solid var(--card-border)' }}>
                  <td className="py-2 px-3 font-medium" style={{ color: 'var(--white)' }}>{row.bucket}</td>
                  <td className="py-2 px-3 text-right" style={{ color: 'var(--light-gray)' }}>{row.count}</td>
                  <td className="py-2 px-3 text-right" style={{ color: 'var(--light-gray)' }}>
                    ${(row.amount / 1e3).toFixed(0)}K
                  </td>
                  <td className="py-2 px-3 text-right" style={{ color: 'var(--light-gray)' }}>
                    {row.percentage.toFixed(1)}%
                  </td>
                  <td className="py-2 px-3">
                    <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--bg-main)' }}>
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${row.percentage}%`,
                          backgroundColor: 'var(--primary-purple)',
                        }}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Collections Trend */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          Collections Trend
        </h3>
        <MultiLineChart
          data={collections_trend}
          xKey="month"
          lines={[
            { dataKey: "collected", name: "Collected", color: "#a78bfa" },
            { dataKey: "target", name: "Target", color: "#6b7280" },
          ]}
          height={280}
        />
      </div>
    </div>
  );
}
