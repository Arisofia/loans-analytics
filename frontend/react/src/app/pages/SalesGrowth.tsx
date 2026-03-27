import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { BarChartComponent, AreaChartComponent } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { TrendingUp, Users, DollarSign, Percent } from "lucide-react";

interface SalesData {
  metrics: {
    new_loans_mtd: number;
    repeat_rate: number;
    cac: number;
    ltv_cac_ratio: number;
  };
  sales_funnel: Array<{
    stage: string;
    count: number;
  }>;
  funnel_rates: {
    application_rate: number;
    approval_rate: number;
  };
  growth_trajectory: Array<{
    month: string;
    disbursements: number;
    target: number;
  }>;
}

export default function SalesGrowth() {
  const { data, loading, error, refetch } = useSection<SalesData>("sales");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { metrics, sales_funnel, funnel_rates, growth_trajectory } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div>
        <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Sales & Growth
        </h1>
        <p style={{ color: 'var(--medium-gray)' }}>
          Origination pipeline and growth analytics
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="New Loans MTD"
          value={metrics.new_loans_mtd.toLocaleString()}
          icon={TrendingUp}
          status="good"
        />
        <MetricCard
          title="Repeat Rate"
          value={`${metrics.repeat_rate.toFixed(1)}%`}
          icon={Users}
          status={metrics.repeat_rate >= 30 ? "good" : "warning"}
        />
        <MetricCard
          title="CAC"
          value={`$${metrics.cac.toFixed(0)}`}
          icon={DollarSign}
          status="neutral"
        />
        <MetricCard
          title="LTV/CAC"
          value={`${metrics.ltv_cac_ratio.toFixed(1)}x`}
          icon={Percent}
          status={metrics.ltv_cac_ratio >= 3 ? "good" : metrics.ltv_cac_ratio >= 2 ? "warning" : "critical"}
        />
      </div>

      {/* Sales Funnel */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold" style={{ color: 'var(--white)' }}>
            Sales Funnel
          </h3>
          {funnel_rates && (
            <div className="flex gap-4 text-xs">
              <span style={{ color: 'var(--medium-gray)' }}>
                Application Rate: <span style={{ color: 'var(--primary-purple)' }}>{funnel_rates.application_rate}%</span>
              </span>
              <span style={{ color: 'var(--medium-gray)' }}>
                Approval Rate: <span style={{ color: 'var(--primary-purple)' }}>{funnel_rates.approval_rate}%</span>
              </span>
            </div>
          )}
        </div>
        <BarChartComponent
          data={sales_funnel}
          xKey="stage"
          yKey="count"
          height={280}
        />
      </div>

      {/* Growth Trajectory */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          Growth Trajectory
        </h3>
        <AreaChartComponent
          data={growth_trajectory}
          xKey="month"
          yKey="disbursements"
          height={280}
        />
      </div>
    </div>
  );
}
