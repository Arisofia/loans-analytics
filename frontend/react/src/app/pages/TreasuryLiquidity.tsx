import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { AreaChartComponent } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { DollarSign, Percent, TrendingUp, BarChart3 } from "lucide-react";

interface TreasuryData {
  metrics: {
    cash_reserve: number;
    liquidity_ratio: number;
    advance_rate: number;
    utilization: number;
  };
  cashflow_projection: Array<{
    week: string;
    inflow: number;
    outflow: number;
    net: number;
  }>;
  eligible_portfolio: Array<{
    category: string;
    amount: number;
    eligible: number;
    rate: number;
  }>;
}

export default function TreasuryLiquidity() {
  const { data, loading, error, refetch } = useSection<TreasuryData>("treasury");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { metrics, cashflow_projection, eligible_portfolio } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div>
        <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Treasury & Liquidity
        </h1>
        <p style={{ color: 'var(--medium-gray)' }}>
          Cash management and funding facility monitoring
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Cash Reserve"
          value={`$${(metrics.cash_reserve / 1e6).toFixed(1)}M`}
          icon={DollarSign}
          status="neutral"
        />
        <MetricCard
          title="Liquidity Ratio"
          value={`${metrics.liquidity_ratio.toFixed(1)}x`}
          icon={Percent}
          status={metrics.liquidity_ratio >= 1.5 ? "good" : metrics.liquidity_ratio >= 1.0 ? "warning" : "critical"}
        />
        <MetricCard
          title="Advance Rate"
          value={`${metrics.advance_rate.toFixed(1)}%`}
          icon={TrendingUp}
          status="neutral"
        />
        <MetricCard
          title="Utilization"
          value={`${metrics.utilization.toFixed(1)}%`}
          icon={BarChart3}
          status={metrics.utilization <= 80 ? "good" : metrics.utilization <= 90 ? "warning" : "critical"}
        />
      </div>

      {/* Cashflow Projection */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          Weekly Cashflow Projection
        </h3>
        <AreaChartComponent
          data={cashflow_projection}
          xKey="week"
          yKey="net"
          height={280}
        />
      </div>

      {/* Eligible Portfolio */}
      {eligible_portfolio && eligible_portfolio.length > 0 && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Eligible Portfolio
          </h3>
          <div className="space-y-4">
            {eligible_portfolio.map((item) => (
              <div key={item.category}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm" style={{ color: 'var(--light-gray)' }}>{item.category}</span>
                  <span className="text-sm font-medium" style={{ color: 'var(--white)' }}>
                    ${(item.eligible / 1e6).toFixed(1)}M / ${(item.amount / 1e6).toFixed(1)}M
                  </span>
                </div>
                <div className="w-full h-3 rounded-full" style={{ backgroundColor: 'var(--bg-main)' }}>
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${item.rate}%`,
                      background: 'var(--gradient-purple)',
                    }}
                  />
                </div>
                <p className="text-xs mt-1" style={{ color: 'var(--medium-gray)' }}>
                  {item.rate.toFixed(1)}% eligible
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
