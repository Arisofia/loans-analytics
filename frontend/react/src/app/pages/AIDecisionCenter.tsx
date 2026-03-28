import { useSection } from "@/hooks/useData";
import { MetricCard, ConfidenceBadge } from "../components/MetricComponents";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Brain, ShieldAlert, TrendingUp, CheckCircle2, Zap, Target } from "lucide-react";

interface AIData {
  business_state: string;
  confidence: number;
  agents: Array<{ name: string; status: "Active" | "Standby" | "Alert"; confidence: number; task: string }>;
  ranked_actions: Array<{ rank: number; action: string; confidence: number; owner: string }>;
  opportunities: Array<{ title: string; estimated_uplift_pct: number }>;
}

const statusDot = (s: string) => ({ Active: "🟢", Standby: "⏳", Alert: "🔴" }[s] ?? "⏳");
const urgColor = (rank: number) =>
  rank <= 2 ? "var(--error)" : rank <= 4 ? "var(--warning)" : "var(--success)";

export default function AIDecisionCenter() {
  const { data, loading, error, refetch } = useSection<AIData>("ai-decision-center");
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const activeAgents = data.agents.filter((a) => a.status === "Active").length;
  const alertAgents = data.agents.filter((a) => a.status === "Alert").length;

  return (
    <div className="p-6 space-y-8 pb-24 md:pb-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 style={{ background: "var(--gradient-title)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            AI Decision Center
          </h1>
          <p style={{ color: "var(--medium-gray)" }}>Agent confidence, ranked actions, and monetizable opportunities</p>
        </div>
        <ConfidenceBadge confidence={data.confidence} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Business State"
          value={data.business_state}
          icon={Brain}
          status={data.business_state === "HEALTHY" ? "good" : data.business_state === "WATCH" ? "warning" : "critical"}
        />
        <MetricCard title="Active Agents" value={activeAgents} icon={CheckCircle2} status="good" />
        <MetricCard
          title="Alert Agents"
          value={alertAgents}
          icon={ShieldAlert}
          status={alertAgents > 0 ? "critical" : "good"}
        />
        <MetricCard title="Actions Queued" value={data.ranked_actions.length} icon={TrendingUp} status="neutral" />
      </div>

      <div className="rounded-xl p-5" style={{ background: "var(--gradient-card-secondary)", border: "1px solid var(--purple-dark)" }}>
        <h2 className="text-base font-semibold mb-4 flex items-center gap-2" style={{ color: "var(--white)" }}>
          <Zap className="h-4 w-4" style={{ color: "var(--primary-purple)" }} /> Ranked Actions
        </h2>
        <div className="space-y-3">
          {data.ranked_actions.map((a) => (
            <div
              key={a.rank}
              className="flex items-start gap-4 rounded-lg p-4"
              style={{ background: "rgba(193,166,255,0.04)", border: "1px solid rgba(95,72,150,0.25)" }}
            >
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                style={{ background: "var(--primary-purple)", color: "#030E19" }}
              >
                {a.rank}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium" style={{ color: "var(--white)" }}>
                  {a.action}
                </p>
                <div className="flex gap-4 mt-1">
                  <span style={{ fontSize: 11, color: urgColor(a.rank) }}>
                    ● {a.rank <= 2 ? "High" : a.rank <= 4 ? "Medium" : "Low"} priority
                  </span>
                  <span style={{ fontSize: 11, color: "var(--medium-gray)" }}>
                    Owner: <strong style={{ color: "var(--light-gray)" }}>{a.owner}</strong>
                  </span>
                  <span style={{ fontSize: 11, color: "var(--primary-purple)" }}>{(a.confidence * 100).toFixed(0)}% confidence</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl p-5" style={{ background: "var(--gradient-card-secondary)", border: "1px solid var(--purple-dark)" }}>
        <h2 className="text-base font-semibold mb-4 flex items-center gap-2" style={{ color: "var(--white)" }}>
          <Target className="h-4 w-4" style={{ color: "var(--success)" }} /> Growth Opportunities
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          {data.opportunities.map((o, i) => (
            <div
              key={i}
              className="rounded-lg p-4"
              style={{ background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.3)" }}
            >
              <p className="text-sm font-semibold mb-2" style={{ color: "var(--success)" }}>
                {o.title}
              </p>
              <div className="flex items-center gap-2">
                <div style={{ flex: 1, height: 4, background: "rgba(16,185,129,0.2)", borderRadius: 2 }}>
                  <div
                    style={{ width: `${Math.min(o.estimated_uplift_pct * 4, 100)}%`, height: "100%", background: "var(--success)", borderRadius: 2 }}
                  />
                </div>
                <span style={{ fontSize: 13, fontWeight: 700, color: "var(--success)" }}>+{o.estimated_uplift_pct}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl p-5" style={{ background: "var(--gradient-card-secondary)", border: "1px solid var(--purple-dark)" }}>
        <h2 className="text-base font-semibold mb-4" style={{ color: "var(--white)" }}>
          Agent Registry
        </h2>
        <div className="grid md:grid-cols-3 gap-3">
          {data.agents.map((a) => (
            <div
              key={a.name}
              className="rounded-lg p-3"
              style={{ background: "rgba(193,166,255,0.04)", border: "1px solid rgba(95,72,150,0.25)" }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span>{statusDot(a.status)}</span>
                <p className="text-sm font-semibold" style={{ color: "var(--white)" }}>
                  {a.name}
                </p>
              </div>
              <p style={{ fontSize: 11, color: "var(--medium-gray)", lineHeight: 1.5 }}>{a.task}</p>
              <div className="flex items-center gap-2 mt-2">
                <div style={{ flex: 1, height: 3, background: "rgba(255,255,255,0.08)", borderRadius: 2 }}>
                  <div
                    style={{
                      width: `${a.confidence * 100}%`,
                      height: "100%",
                      borderRadius: 2,
                      background:
                        a.confidence > 0.85 ? "var(--success)" : a.confidence > 0.7 ? "var(--warning)" : "var(--error)",
                    }}
                  />
                </div>
                <span style={{ fontSize: 10, color: "var(--medium-gray)" }}>{(a.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
