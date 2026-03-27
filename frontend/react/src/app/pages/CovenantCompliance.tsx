import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { TrendChart } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Button } from "@/components/ui/button";
import { Shield, Percent, TrendingUp, DollarSign, FileText, Send, Clock } from "lucide-react";

interface CovenantData {
  metrics: {
    advance_rate: number;
    dscr: number;
    max_default: number;
    collection_rate: number;
  };
  compliance_status: string;
  repline_distribution: Array<{
    category: string;
    amount: number;
    limit: number;
    utilization: number;
    status: string;
  }>;
  collection_rate_trend: Array<{
    month: string;
    rate: number;
    threshold: number;
  }>;
  covenants: Array<{
    name: string;
    current: number;
    threshold: number;
    status: string;
    description: string;
  }>;
}

export default function CovenantCompliance() {
  const { data, loading, error, refetch } = useSection<CovenantData>("covenants");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { metrics, compliance_status, repline_distribution, collection_rate_trend, covenants } = data;

  const statusColor = compliance_status === "COMPLIANT" ? "text-emerald-400" : "text-red-400";
  const statusBg = compliance_status === "COMPLIANT" ? "bg-emerald-500/20" : "bg-red-500/20";

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Covenant Compliance
          </h1>
          <p style={{ color: 'var(--medium-gray)' }}>
            Funding facility covenant monitoring and lender reporting
          </p>
        </div>
        <span className={`text-sm font-bold px-4 py-2 rounded-full ${statusColor} ${statusBg}`}>
          {compliance_status}
        </span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Advance Rate"
          value={`${metrics.advance_rate.toFixed(1)}%`}
          icon={TrendingUp}
          status={metrics.advance_rate <= 80 ? "good" : metrics.advance_rate <= 85 ? "warning" : "critical"}
        />
        <MetricCard
          title="DSCR"
          value={`${metrics.dscr.toFixed(2)}x`}
          icon={Shield}
          status={metrics.dscr >= 1.25 ? "good" : metrics.dscr >= 1.0 ? "warning" : "critical"}
        />
        <MetricCard
          title="Max Default"
          value={`${metrics.max_default.toFixed(2)}%`}
          icon={Percent}
          status={metrics.max_default <= 5 ? "good" : metrics.max_default <= 8 ? "warning" : "critical"}
        />
        <MetricCard
          title="Collection Rate"
          value={`${metrics.collection_rate.toFixed(1)}%`}
          icon={DollarSign}
          status={metrics.collection_rate >= 95 ? "good" : metrics.collection_rate >= 85 ? "warning" : "critical"}
        />
      </div>

      {/* Repline Distribution */}
      {repline_distribution && repline_distribution.length > 0 && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Repline Distribution
          </h3>
          <div className="space-y-4">
            {repline_distribution.map((item) => (
              <div key={item.category}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm" style={{ color: 'var(--light-gray)' }}>{item.category}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-sm" style={{ color: 'var(--white)' }}>
                      ${(item.amount / 1e6).toFixed(1)}M / ${(item.limit / 1e6).toFixed(1)}M
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      item.status === 'OK' ? 'bg-emerald-500/20 text-emerald-400' :
                      item.status === 'WARNING' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {item.status}
                    </span>
                  </div>
                </div>
                <div className="relative w-full h-3 rounded-full" style={{ backgroundColor: 'var(--bg-main)' }}>
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(item.utilization, 100)}%`,
                      background: item.utilization > 90 ? '#ef4444' :
                                 item.utilization > 75 ? '#f59e0b' :
                                 'var(--gradient-purple)',
                    }}
                  />
                  {/* Threshold marker */}
                  <div
                    className="absolute top-0 h-full w-0.5 bg-white/50"
                    style={{ left: '80%' }}
                  />
                </div>
                <p className="text-xs mt-1" style={{ color: 'var(--medium-gray)' }}>
                  {item.utilization.toFixed(1)}% utilized
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Collection Rate Trend */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          Collection Rate Trend
        </h3>
        <TrendChart
          data={collection_rate_trend}
          xKey="month"
          yKey="rate"
          height={280}
        />
      </div>

      {/* Covenants List */}
      {covenants && covenants.length > 0 && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Covenant Details
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Covenant</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Current</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Threshold</th>
                  <th className="text-center py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {covenants.map((cov) => (
                  <tr key={cov.name} style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <td className="py-2 px-3">
                      <p style={{ color: 'var(--white)' }}>{cov.name}</p>
                      <p className="text-xs" style={{ color: 'var(--medium-gray)' }}>{cov.description}</p>
                    </td>
                    <td className="py-2 px-3 text-right font-mono" style={{ color: 'var(--light-gray)' }}>
                      {cov.current}
                    </td>
                    <td className="py-2 px-3 text-right font-mono" style={{ color: 'var(--medium-gray)' }}>
                      {cov.threshold}
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        cov.status === 'PASS' ? 'bg-emerald-500/20 text-emerald-400' :
                        cov.status === 'WATCH' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {cov.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Lender Pack */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          Lender Pack
        </h3>
        <p className="text-sm mb-4" style={{ color: 'var(--medium-gray)' }}>
          Generate and distribute lender compliance reports
        </p>
        <div className="flex gap-3 flex-wrap">
          <Button size="sm" className="gap-2">
            <FileText className="h-4 w-4" />
            Generate PDF
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Send className="h-4 w-4" />
            Send to Lender
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Clock className="h-4 w-4" />
            Schedule
          </Button>
        </div>
      </div>
    </div>
  );
}
