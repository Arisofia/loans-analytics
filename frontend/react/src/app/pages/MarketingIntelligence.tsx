import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Target, TrendingUp, PieChart, Users } from "lucide-react";

interface MarketingData {
  metrics: {
    cac: number;
    ltv: number;
    ltv_cac_ratio: number;
    invisible_primes: number;
    invisible_primes_default_rate: number;
  };
  channels: Array<{
    channel: string;
    cac: number;
    ltv: number;
    ltv_cac: number;
    conversion: number;
  }>;
  segments: Array<{
    segment: string;
    borrowers: number;
    default_rate: number;
    avg_ticket: number;
  }>;
}

export default function MarketingIntelligence() {
  const { data, loading, error, refetch } = useSection<MarketingData>("marketing");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const bestChannel = [...data.channels].sort((a, b) => b.ltv_cac - a.ltv_cac)[0];

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      <div>
        <h1 style={{ background: "var(--gradient-title)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Marketing Intelligence
        </h1>
        <p style={{ color: "var(--medium-gray)" }}>
          CAC/LTV dynamics, channel economics, and invisible-prime growth intelligence.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard title="CAC" value={`$${data.metrics.cac.toFixed(1)}`} icon={Target} status={data.metrics.cac < 130 ? "good" : "warning"} />
        <MetricCard title="LTV" value={`$${data.metrics.ltv.toFixed(1)}`} icon={TrendingUp} status="good" />
        <MetricCard title="LTV/CAC" value={`${data.metrics.ltv_cac_ratio.toFixed(1)}x`} icon={PieChart} status={data.metrics.ltv_cac_ratio > 4 ? "good" : "warning"} />
        <MetricCard title="Invisible Primes" value={data.metrics.invisible_primes} icon={Users} status="neutral" />
      </div>

      <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
        <h3 className="text-sm font-semibold mb-2" style={{ color: "var(--white)" }}>Invisible Primes Signal</h3>
        <p className="text-xs" style={{ color: "var(--medium-gray)" }}>
          {data.metrics.invisible_primes} thin-file borrowers currently outperform with a {data.metrics.invisible_primes_default_rate}% default rate.
          This segment remains below portfolio loss expectations and is prioritized for controlled scaling.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Channel Economics</h3>
          <div className="space-y-3">
            {data.channels.map((row) => (
              <div key={row.channel} className="rounded-lg border border-gray-800 p-3">
                <div className="flex justify-between text-xs mb-2">
                  <span style={{ color: "var(--light-gray)" }}>{row.channel}</span>
                  <span style={{ color: row.channel === bestChannel.channel ? "#34d399" : "var(--medium-gray)" }}>
                    LTV/CAC {row.ltv_cac.toFixed(1)}x
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[11px]" style={{ color: "var(--medium-gray)" }}>
                  <span>CAC ${row.cac.toFixed(1)}</span>
                  <span>LTV ${row.ltv.toFixed(1)}</span>
                  <span>Conv {row.conversion.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Segment Matrix</h3>
          <div className="space-y-3">
            {data.segments.map((row) => (
              <div key={row.segment} className="grid grid-cols-4 gap-2 text-xs border-b border-gray-800 pb-2 last:border-0">
                <span style={{ color: "var(--light-gray)" }}>{row.segment}</span>
                <span style={{ color: "var(--medium-gray)" }}>{row.borrowers} borrowers</span>
                <span style={{ color: "var(--medium-gray)" }}>DR {row.default_rate}%</span>
                <span style={{ color: "var(--medium-gray)" }}>Avg ${row.avg_ticket}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
