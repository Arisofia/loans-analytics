import { useState } from "react";
import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { MultiLineChart, BarChartComponent } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Button } from "@/components/ui/button";
import { Activity, TrendingDown, RefreshCw, Percent } from "lucide-react";

interface VintageData {
  metrics: {
    avg_mob: number;
    vintage_default: number;
    roll_rate_30_60: number;
    cure_rate: number;
  };
  vintage_curves: Array<Record<string, number | string>>;
  vintage_lines: Array<{
    key: string;
    name: string;
    color: string;
  }>;
  roll_rate_matrix: Array<{
    from: string;
    to: string;
    rate: number;
  }>;
  cohort_performance: Array<{
    cohort: string;
    disbursed: number;
    default_rate: number;
    recovery_rate: number;
  }>;
}

export default function VintageAnalysis() {
  const [period, setPeriod] = useState<"monthly" | "quarterly">("monthly");
  const { data, loading, error, refetch } = useSection<VintageData>("vintage");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { metrics, vintage_curves, vintage_lines, roll_rate_matrix, cohort_performance } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Vintage & Cohort Analysis
          </h1>
          <p style={{ color: 'var(--medium-gray)' }}>
            Historical performance tracking by origination cohort
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={period === "monthly" ? "default" : "outline"}
            size="sm"
            onClick={() => setPeriod("monthly")}
          >
            Monthly
          </Button>
          <Button
            variant={period === "quarterly" ? "default" : "outline"}
            size="sm"
            onClick={() => setPeriod("quarterly")}
          >
            Quarterly
          </Button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Avg MOB"
          value={metrics.avg_mob.toFixed(1)}
          icon={Activity}
          status="neutral"
        />
        <MetricCard
          title="Vintage Default"
          value={`${metrics.vintage_default.toFixed(2)}%`}
          icon={TrendingDown}
          status={metrics.vintage_default > 5 ? "critical" : metrics.vintage_default > 3 ? "warning" : "good"}
        />
        <MetricCard
          title="Roll Rate 30→60"
          value={`${metrics.roll_rate_30_60.toFixed(1)}%`}
          icon={RefreshCw}
          status={metrics.roll_rate_30_60 > 20 ? "critical" : metrics.roll_rate_30_60 > 10 ? "warning" : "good"}
        />
        <MetricCard
          title="Cure Rate"
          value={`${metrics.cure_rate.toFixed(1)}%`}
          icon={Percent}
          status={metrics.cure_rate >= 40 ? "good" : metrics.cure_rate >= 25 ? "warning" : "critical"}
        />
      </div>

      {/* Vintage Curves */}
      {vintage_curves && vintage_lines && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Vintage Default Rate Curves
          </h3>
          <MultiLineChart
            data={vintage_curves}
            xKey="mob"
            lines={vintage_lines}
            height={320}
          />
        </div>
      )}

      {/* Roll Rate Matrix */}
      {roll_rate_matrix && roll_rate_matrix.length > 0 && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Roll Rate Matrix
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>From</th>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>To</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Rate</th>
                </tr>
              </thead>
              <tbody>
                {roll_rate_matrix.map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <td className="py-2 px-3" style={{ color: 'var(--white)' }}>{row.from}</td>
                    <td className="py-2 px-3" style={{ color: 'var(--light-gray)' }}>{row.to}</td>
                    <td className="py-2 px-3 text-right">
                      <span className={
                        row.rate > 20 ? 'text-red-400' :
                        row.rate > 10 ? 'text-amber-400' :
                        'text-emerald-400'
                      }>
                        {row.rate.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Cohort Performance */}
      {cohort_performance && cohort_performance.length > 0 && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Cohort Performance
          </h3>
          <BarChartComponent
            data={cohort_performance}
            xKey="cohort"
            yKey="default_rate"
            height={250}
          />
          <div className="overflow-x-auto mt-4">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Cohort</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Disbursed</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Default Rate</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Recovery</th>
                </tr>
              </thead>
              <tbody>
                {cohort_performance.map((row) => (
                  <tr key={row.cohort} style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <td className="py-2 px-3" style={{ color: 'var(--white)' }}>{row.cohort}</td>
                    <td className="py-2 px-3 text-right" style={{ color: 'var(--light-gray)' }}>
                      ${(row.disbursed / 1e6).toFixed(1)}M
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className={row.default_rate > 5 ? 'text-red-400' : row.default_rate > 3 ? 'text-amber-400' : 'text-emerald-400'}>
                        {row.default_rate.toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right" style={{ color: 'var(--light-gray)' }}>
                      {row.recovery_rate.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
