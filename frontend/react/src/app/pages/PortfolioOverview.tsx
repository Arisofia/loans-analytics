import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { AreaChartComponent, DonutChart } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { DollarSign, BarChart3, Percent, TrendingDown } from "lucide-react";

interface PortfolioData {
  metrics: {
    aum: number;
    active_loans: number;
    avg_apr: number;
    default_rate: number;
  };
  outstanding_trend: Array<{
    month: string;
    outstanding: number;
  }>;
  status_distribution: Array<{
    name: string;
    value: number;
    color: string;
  }>;
}

export default function PortfolioOverview() {
  const { data, loading, error, refetch } = useSection<PortfolioData>("portfolio");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { metrics, outstanding_trend, status_distribution } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div>
        <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Portfolio Overview
        </h1>
        <p style={{ color: 'var(--medium-gray)' }}>
          Comprehensive view of your lending portfolio
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Assets Under Management"
          value={`$${(metrics.aum / 1e6).toFixed(1)}M`}
          icon={DollarSign}
          status="neutral"
        />
        <MetricCard
          title="Active Loans"
          value={metrics.active_loans.toLocaleString()}
          icon={BarChart3}
          status="good"
        />
        <MetricCard
          title="Avg APR"
          value={`${metrics.avg_apr.toFixed(1)}%`}
          icon={Percent}
          status="neutral"
        />
        <MetricCard
          title="Default Rate"
          value={`${metrics.default_rate.toFixed(2)}%`}
          icon={TrendingDown}
          status={metrics.default_rate > 5 ? "critical" : metrics.default_rate > 3 ? "warning" : "good"}
        />
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Outstanding Balance (Monthly)
          </h3>
          <AreaChartComponent
            data={outstanding_trend}
            xKey="month"
            yKey="outstanding"
            height={280}
          />
        </div>

        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Loan Status Distribution
          </h3>
          <DonutChart data={status_distribution} height={280} />
        </div>
      </div>
    </div>
  );
}
