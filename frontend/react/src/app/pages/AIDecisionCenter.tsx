import { useSection } from "@/hooks/useData";
import { MetricCard, ConfidenceBadge } from "../components/MetricComponents";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Brain, ShieldAlert, TrendingUp, CheckCircle2 } from "lucide-react";

interface AIData {
  business_state: string;
  confidence: number;
  agents: Array<{
    name: string;
    status: "Active" | "Standby" | "Alert";
    confidence: number;
    task: string;
  }>;
  ranked_actions: Array<{
    rank: number;
    action: string;
    confidence: number;
    owner: string;
  }>;
  opportunities: Array<{
    title: string;
    estimated_uplift_pct: number;
  }>;
}

export default function AIDecisionCenter() {
  const { data, loading, error, refetch } = useSection<AIData>("ai-decision-center");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const activeAgents = data.agents.filter((a) => a.status === "Active").length;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 style={{ background: "var(--gradient-title)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            AI Decision Center
          </h1>
          <p style={{ color: "var(--medium-gray)" }}>Agent confidence, ranked actions, and monetizable AI opportunities.</p>
        </div>
        <ConfidenceBadge confidence={data.confidence} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Business State" value={data.business_state} icon={Brain} status={data.business_state === "WATCH" ? "warning" : "good"} />
        <MetricCard title="Active Agents" value={activeAgents} icon={CheckCircle2} status="good" />
        <MetricCard title="Top Action Confidence" value={`${Math.round(data.ranked_actions[0]?.confidence * 100 || 0)}%`} icon={ShieldAlert} status="warning" />
        <MetricCard title="Opportunities" value={data.opportunities.length} icon={TrendingUp} status="neutral" />
      </div>

      <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Agent Grid</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.agents.map((agent) => (
            <div key={agent.name} className="rounded-lg border border-gray-800 p-3">
              <div className="flex justify-between text-xs mb-2">
                <span style={{ color: "var(--light-gray)" }}>{agent.name}</span>
                <span className={agent.status === "Alert" ? "text-red-400" : agent.status === "Standby" ? "text-amber-400" : "text-emerald-400"}>
                  {agent.status}
                </span>
              </div>
              <div className="h-2 rounded bg-gray-900 overflow-hidden mb-2">
                <div className="h-full bg-indigo-500" style={{ width: `${Math.round(agent.confidence * 100)}%` }} />
              </div>
              <p className="text-[11px]" style={{ color: "var(--medium-gray)" }}>{agent.task}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Ranked Actions</h3>
          <div className="space-y-3">
            {data.ranked_actions.map((item) => (
              <div key={item.rank} className="grid grid-cols-6 gap-2 text-xs border-b border-gray-800 pb-2 last:border-0">
                <span style={{ color: "var(--primary-purple)" }}>#{item.rank}</span>
                <span className="col-span-3" style={{ color: "var(--light-gray)" }}>{item.action}</span>
                <span style={{ color: "var(--medium-gray)" }}>{Math.round(item.confidence * 100)}%</span>
                <span style={{ color: "var(--medium-gray)" }}>{item.owner}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl p-5" style={{ backgroundColor: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--white)" }}>Growth Opportunities</h3>
          <div className="space-y-3">
            {data.opportunities.map((item) => (
              <div key={item.title} className="rounded-lg border border-gray-800 p-3 flex justify-between text-xs">
                <span style={{ color: "var(--light-gray)" }}>{item.title}</span>
                <span style={{ color: "#34d399" }}>+{item.estimated_uplift_pct}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
