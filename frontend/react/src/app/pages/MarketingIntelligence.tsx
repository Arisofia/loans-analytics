import { useSection } from "@/hooks/useData";
import { MetricCard, AlertCard } from "../components/MetricComponents";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { BarChartComponent, PieChartComponent } from "../components/Charts";
import { Target, Users, Megaphone, TrendingUp } from "lucide-react";

interface MarketingData {
  metrics: {
    cac: number;
    ltv_cac_ratio: number;
    conversion_rate: number;
    roi: number;
  };
  segment_performance: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  channel_efficiency: Array<{
    channel: string;
    cac: number;
    conversion: number;
  }>;
}

export default function MarketingIntelligence() {
  const { data, loading, error, refetch } = useSection<MarketingData>("marketing");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { metrics, segment_performance, channel_efficiency } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div>
        <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Marketing Intelligence
        </h1>
        <p style={{ color: 'var(--medium-gray)' }}>
          Campaign performance and acquisition efficiency
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="CAC"
          value={`$${metrics.cac.toFixed(0)}`}
          icon={Target}
          status={metrics.cac < 150 ? "good" : "warning"}
        />
        <MetricCard
          title="LTV / CAC"
          value={`${metrics.ltv_cac_ratio.toFixed(1)}x`}
          icon={TrendingUp}
          status={metrics.ltv_cac_ratio > 3 ? "good" : "warning"}
        />
        <MetricCard
          title="Conv. Rate"
          value={`${metrics.conversion_rate.toFixed(1)}%`}
          icon={Users}
          status="neutral"
        />
        <MetricCard
          title="Marketing ROI"
          value={`${metrics.roi.toFixed(1)}x`}
          icon={Megaphone}
          status="good"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Segment Performance */}
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Segment Distribution
          </h3>
          <PieChartComponent
            data={segment_performance}
            height={280}
          />
        </div>

        {/* Channel Efficiency */}
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Channel Efficiency (CAC)
          </h3>
          <BarChartComponent
            data={channel_efficiency}
            xKey="channel"
            yKey="cac"
            height={280}
          />
        </div>
      </div>
    </div>
  );
}
