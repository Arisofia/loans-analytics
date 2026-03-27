import { useSection } from "@/hooks/useData";
import { MetricCard, AlertCard, ConfidenceBadge } from "../components/MetricComponents";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Brain, ListChecks, Bell, ShieldAlert } from "lucide-react";

interface DecisionData {
  business_state: string;
  confidence: number;
  agent_statuses: Record<string, string>;
  critical_alerts: Array<{
    alert_id: string;
    title: string;
    description: string;
    severity: string;
    current_value?: number;
    threshold?: number;
  }>;
  ranked_actions: Array<{
    action_id: string;
    title: string;
    details: string;
    owner: string;
    urgency: string;
    confidence: number;
  }>;
}

export default function AIDecisionCenter() {
  const { data, loading, error, refetch } = useSection<DecisionData>("decision");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { business_state, confidence, agent_statuses, critical_alerts, ranked_actions } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            AI Decision Center
          </h1>
          <p style={{ color: 'var(--medium-gray)' }}>
            Consolidated outputs from the multi-agent decision intelligence system
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-bold px-3 py-1 rounded-full border ${
            business_state === "HEALTHY" ? "text-emerald-400 border-emerald-400" :
            business_state === "WATCH" ? "text-amber-400 border-amber-400" :
            "text-red-400 border-red-400"
          }`}
                style={{ backgroundColor: 'rgba(0,0,0,0.3)' }}>
            {business_state}
          </span>
          <ConfidenceBadge confidence={confidence} />
        </div>
      </div>

      {/* Agent Status Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {Object.entries(agent_statuses).map(([agent, status]) => (
          <div key={agent} className="rounded-lg p-3 border border-gray-800" style={{ backgroundColor: 'var(--card-bg)' }}>
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{agent.replace('_', ' ')}</div>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                status === "ok" ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" :
                status === "blocked" ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]" :
                "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]"
              }`} />
              <span className="text-xs font-semibold uppercase" style={{ color: 'var(--light-gray)' }}>{status}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Critical Alerts */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-500" />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--white)' }}>
              Critical Alerts
            </h3>
          </div>
          <div className="space-y-3">
            {critical_alerts.length > 0 ? (
              critical_alerts.map((alert, idx) => (
                <AlertCard
                  key={idx}
                  type={alert.severity as any}
                  message={`${alert.title}: ${alert.description}`}
                />
              ))
            ) : (
              <div className="text-xs text-gray-500 italic p-4 rounded-lg border border-dashed border-gray-800">
                No active critical alerts detected by the agents.
              </div>
            )}
          </div>
        </div>

        {/* Ranked Actions */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <ListChecks className="h-5 w-5 text-indigo-500" />
            <h3 className="text-sm font-semibold" style={{ color: 'var(--white)' }}>
              Recommended Strategic Actions
            </h3>
          </div>
          <div className="space-y-3">
            {ranked_actions.map((action, idx) => (
              <div key={idx} className="rounded-xl p-4 border border-gray-800" style={{ backgroundColor: 'var(--card-bg)' }}>
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-sm font-bold" style={{ color: 'var(--white)' }}>{action.title}</h4>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                    action.urgency === "high" ? "bg-red-500/10 text-red-400" :
                    action.urgency === "medium" ? "bg-amber-500/10 text-amber-400" :
                    "bg-blue-500/10 text-blue-400"
                  }`}>
                    {action.urgency}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mb-3">{action.details}</p>
                <div className="flex justify-between items-center text-[10px]">
                  <span style={{ color: 'var(--medium-gray)' }}>Owner: <span style={{ color: 'var(--primary-purple)' }}>{action.owner}</span></span>
                  <span style={{ color: 'var(--medium-gray)' }}>Confidence: <span style={{ color: 'var(--white)' }}>{(action.confidence * 100).toFixed(0)}%</span></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
