import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { BarChartComponent } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { TrendingUp, Users, DollarSign, Percent } from "lucide-react";

interface MarketingData {
  summary: { cac: number; ltv: number; roi: number; avg_ticket: number };
  channel_performance: Array<{ channel: string; leads: number; funded: number; cac: number; quality: string }>;
  segment_performance: Array<{ segment: string; count: number; avg_ticket: number; default_rate: number; ltv: number; roi: number }>;
  invisible_primes: { count: number; description: string; avg_dpd: number; avg_ticket: number };
}

const qColor = (q: string) => ({ high: "var(--success)", medium: "var(--warning)", low: "var(--error)" }[q] ?? "var(--medium-gray)");

export default function MarketingIntelligence() {
  const { data, loading, error, refetch } = useSection<MarketingData>("marketing");
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;
  const { summary, channel_performance, segment_performance, invisible_primes } = data;

  const segChart = segment_performance.map(s => ({ name: s.segment, default_rate: s.default_rate, roi: s.roi / 100 }));
  const chanChart = channel_performance.map(c => ({ name: c.channel, funded: c.funded, cac: c.cac }));

  return (
    <div className="p-6 space-y-8 pb-24 md:pb-6">
      <div>
        <h1 style={{ background: "var(--gradient-title)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Marketing Intelligence
        </h1>
        <p style={{ color: "var(--medium-gray)" }}>CAC, LTV, channel ROI, and segment growth opportunities</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard title="CAC" value={`$${summary.cac}`} icon={DollarSign}
          status={summary.cac < 100 ? "good" : summary.cac < 150 ? "warning" : "critical"} />
        <MetricCard title="LTV" value={`$${summary.ltv.toLocaleString()}`} icon={TrendingUp} status="good" />
        <MetricCard title="LTV/CAC" value={`${(summary.ltv / summary.cac).toFixed(1)}x`} icon={Percent}
          status={summary.ltv / summary.cac >= 3 ? "good" : "warning"} />
        <MetricCard title="Avg Ticket" value={`$${summary.avg_ticket.toLocaleString()}`} icon={Users} status="neutral" />
      </div>

      {/* Invisible Primes highlight */}
      <div className="rounded-xl p-5 flex gap-5 items-center"
           style={{ background: "var(--gradient-card-primary)", border: "1px solid var(--primary-purple)" }}>
        <div style={{ fontSize: 40, flexShrink: 0 }}>✨</div>
        <div className="flex-1">
          <p className="text-base font-semibold" style={{ color: "var(--primary-purple)" }}>Invisible Primes Opportunity</p>
          <p style={{ fontSize: 12, color: "var(--light-gray)", marginTop: 4 }}>{invisible_primes.description}</p>
        </div>
        <div className="grid grid-cols-3 gap-6">
          {[
            { l: "Identified", v: invisible_primes.count },
            { l: "Avg DPD", v: invisible_primes.avg_dpd },
            { l: "Avg Ticket", v: `$${invisible_primes.avg_ticket.toLocaleString()}` },
          ].map(item => (
            <div key={item.l} className="text-center">
              <p style={{ fontSize: 10, color: "var(--medium-gray)", textTransform: "uppercase", letterSpacing: "0.05em" }}>{item.l}</p>
              <p className="text-2xl font-bold" style={{ color: "var(--white)" }}>{item.v}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Channel performance */}
        <div className="rounded-xl p-5" style={{ background: "var(--gradient-card-secondary)", border: "1px solid var(--purple-dark)" }}>
          <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Channel: Funded Loans</h2>
          <BarChartComponent data={chanChart} xKey="name" bars={[
            { dataKey: "funded", name: "Funded", color: "#C1A6FF" },
          ]} height={220} />
          <div className="mt-4 space-y-2">
            {channel_performance.map(c => (
              <div key={c.channel} className="flex items-center gap-3">
                <span style={{ minWidth: 100, fontSize: 12, color: "var(--light-gray)" }}>{c.channel}</span>
                <div style={{ flex: 1, height: 5, background: "rgba(255,255,255,0.08)", borderRadius: 3 }}>
                  <div style={{ width: `${(c.funded / c.leads * 100)}%`, height: "100%", background: qColor(c.quality), borderRadius: 3 }} />
                </div>
                <span style={{ fontSize: 11, color: "var(--medium-gray)", minWidth: 60, textAlign: "right" }}>
                  {(c.funded / c.leads * 100).toFixed(1)}% · CAC ${c.cac}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Segment ROI */}
        <div className="rounded-xl p-5" style={{ background: "var(--gradient-card-secondary)", border: "1px solid var(--purple-dark)" }}>
          <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Segment: Default % vs ROI Index</h2>
          <BarChartComponent data={segChart} xKey="name" bars={[
            { dataKey: "roi",          name: "ROI index",    color: "#C1A6FF" },
            { dataKey: "default_rate", name: "Default %",    color: "#ef4444" },
          ]} height={220} />
        </div>
      </div>

      {/* Segment table */}
      <div className="rounded-xl p-5" style={{ background: "var(--gradient-card-secondary)", border: "1px solid var(--purple-dark)" }}>
        <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Segment Intelligence</h2>
        <div className="overflow-x-auto">
          <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(95,72,150,0.4)" }}>
                {["Segment","Loans","Avg Ticket","Default %","LTV","ROI %","Rec."].map(h => (
                  <th key={h} style={{ padding:"8px 10px", textAlign:"left", color:"var(--medium-gray)", fontWeight:500, fontSize:11, textTransform:"uppercase", letterSpacing:"0.05em" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {segment_performance.map(s => (
                <tr key={s.segment} style={{ borderBottom: "1px solid rgba(95,72,150,0.15)" }}>
                  <td style={{ padding:"8px 10px", color:"var(--white)", fontWeight:500 }}>{s.segment}</td>
                  <td style={{ padding:"8px 10px", color:"var(--light-gray)" }}>{s.count}</td>
                  <td style={{ padding:"8px 10px", color:"var(--light-gray)" }}>${s.avg_ticket.toLocaleString()}</td>
                  <td style={{ padding:"8px 10px", color: s.default_rate > 2.5 ? "var(--error)" : s.default_rate > 1.5 ? "var(--warning)" : "var(--success)" }}>
                    {s.default_rate.toFixed(1)}%
                  </td>
                  <td style={{ padding:"8px 10px", color:"var(--primary-purple)" }}>${s.ltv.toLocaleString()}</td>
                  <td style={{ padding:"8px 10px", color: s.roi > 2000 ? "var(--success)" : "var(--light-gray)" }}>
                    {s.roi.toFixed(0)}%
                  </td>
                  <td style={{ padding:"8px 10px" }}>
                    <span style={{ fontSize:10, padding:"2px 8px", borderRadius:4,
                                   background: s.roi > 2000 ? "rgba(16,185,129,0.15)" : s.default_rate > 2.5 ? "rgba(220,38,38,0.12)" : "rgba(95,72,150,0.2)",
                                   color: s.roi > 2000 ? "var(--success)" : s.default_rate > 2.5 ? "var(--error)" : "var(--medium-gray)" }}>
                      {s.roi > 2000 ? "SCALE" : s.default_rate > 2.5 ? "WATCH" : "HOLD"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
