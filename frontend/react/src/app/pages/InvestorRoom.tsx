import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { ShieldAlert, TrendingUp, DollarSign, Scale } from "lucide-react";

interface InvestorRoomData {
  covenant_monitoring: Array<{
    covenant: string;
    current: number;
    threshold: number;
    status: "PASS" | "WATCH" | "BREACH";
    headroom: number;
  }>;
  scenarios: Array<{
    name: string;
    weight: number;
    irr: number;
    expected_loss: number;
    par30: number;
  }>;
  corrected_metrics: {
    ppc: number;
    ppp: number;
    ppc_ppp_gap: number;
  };
  cohort_table: Array<{
    vintage: string;
    disbursed: number;
    irr: number;
    expected_loss: number;
  }>;
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);

export default function InvestorRoom() {
  const { data, loading, error, refetch } = useSection<InvestorRoomData>("investor-room");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const breaches = data.covenant_monitoring.filter((item) => item.status === "BREACH").length;
  const weightedIrr = data.scenarios.reduce((acc, row) => acc + row.irr * row.weight, 0);

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      <div>
        <h1 style={{ background: "var(--gradient-title)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Investor Room
        </h1>
        <p style={{ color: "var(--medium-gray)" }}>Covenant oversight, downside scenarios, and corrected payout economics.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Covenant Breaches" value={breaches} icon={ShieldAlert} status={breaches > 0 ? "critical" : "good"} />
        <MetricCard title="Weighted IRR" value={`${weightedIrr.toFixed(1)}%`} icon={TrendingUp} status={weightedIrr >= 17 ? "good" : "warning"} />
        <MetricCard title="Corrected PPC" value={`$${data.corrected_metrics.ppc.toFixed(1)}`} icon={DollarSign} status="neutral" />
        <MetricCard title="PPC/PPP Gap" value={`$${data.corrected_metrics.ppc_ppp_gap.toFixed(1)}`} icon={Scale} status="warning" />
      </div>

      <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>
          Covenant Monitoring
        </h3>
        <div className="space-y-3">
          {data.covenant_monitoring.map((row) => {
            const progress = Math.min(100, Math.max(0, (row.current / row.threshold) * 100));
            const tone = row.status === "BREACH" ? "bg-red-500" : row.status === "WATCH" ? "bg-amber-500" : "bg-emerald-500";
            return (
              <div key={row.covenant} className="rounded-lg p-3 border border-gray-800">
                <div className="flex justify-between text-xs mb-2">
                  <span style={{ color: "var(--light-gray)" }}>{row.covenant}</span>
                  <span className={row.status === "BREACH" ? "text-red-400" : row.status === "WATCH" ? "text-amber-400" : "text-emerald-400"}>
                    {row.status}
                  </span>
                </div>
                <div className="h-2 rounded bg-gray-900 overflow-hidden mb-2">
                  <div className={`h-full ${tone}`} style={{ width: `${progress}%` }} />
                </div>
                <div className="text-[11px] flex justify-between" style={{ color: "var(--medium-gray)" }}>
                  <span>Current: {row.current}</span>
                  <span>Threshold: {row.threshold}</span>
                  <span>Headroom: {row.headroom.toFixed(2)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Scenario Matrix</h3>
          <div className="space-y-3">
            {data.scenarios.map((scenario) => (
              <div key={scenario.name} className="grid grid-cols-4 gap-2 text-xs border-b border-gray-800 pb-2 last:border-0">
                <span style={{ color: "var(--light-gray)" }}>{scenario.name}</span>
                <span style={{ color: "var(--medium-gray)" }}>Weight {Math.round(scenario.weight * 100)}%</span>
                <span style={{ color: "var(--medium-gray)" }}>IRR {scenario.irr}%</span>
                <span style={{ color: "var(--medium-gray)" }}>EL {scenario.expected_loss}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Vintage Cohorts</h3>
          <div className="space-y-3">
            {data.cohort_table.map((row) => (
              <div key={row.vintage} className="grid grid-cols-4 gap-2 text-xs border-b border-gray-800 pb-2 last:border-0">
                <span style={{ color: "var(--light-gray)" }}>{row.vintage}</span>
                <span style={{ color: "var(--medium-gray)" }}>{formatCurrency(row.disbursed)}</span>
                <span style={{ color: "var(--medium-gray)" }}>IRR {row.irr}%</span>
                <span style={{ color: "var(--medium-gray)" }}>EL {row.expected_loss}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
