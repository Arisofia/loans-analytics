import { useSection } from "@/hooks/useData";
import { MetricCard, ConfidenceBadge, AlertCard } from "../components/MetricComponents";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Button } from "@/components/ui/button";
import {
  Activity,
  TrendingUp,
  Shield,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

interface ExecutiveData {
  business_state: string;
  confidence: number;
  kpis: {
    portfolio_health: number;
    revenue_trend: string;
    risk_score: number;
    liquidity_ratio: number;
  };
  alerts: Array<{
    id: string;
    type: string;
    message: string;
    severity: string;
    action: string;
  }>;
  prioritized_actions: Array<{
    priority: number;
    agent: string;
    action: string;
    routed_to: string;
  }>;
}

export default function ExecutiveCommandCenter() {
  const { data, loading, error, refetch } = useSection<ExecutiveData>("executive");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { business_state, confidence, kpis, alerts, prioritized_actions } = data;

  const stateColor = business_state === "HEALTHY"
    ? "text-emerald-400"
    : business_state === "WATCH"
      ? "text-amber-400"
      : "text-red-400";

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Executive Command Center
          </h1>
          <p style={{ color: 'var(--medium-gray)' }}>
            AI-powered business intelligence
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-bold px-3 py-1 rounded-full border ${stateColor}`}
                style={{ borderColor: 'currentColor', backgroundColor: 'rgba(0,0,0,0.3)' }}>
            {business_state}
          </span>
          <ConfidenceBadge confidence={confidence} />
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Portfolio Health"
          value={`${kpis.portfolio_health}%`}
          icon={Activity}
          status={kpis.portfolio_health >= 80 ? "good" : kpis.portfolio_health >= 60 ? "warning" : "critical"}
        />
        <MetricCard
          title="Revenue Trend"
          value={kpis.revenue_trend}
          icon={TrendingUp}
          status="good"
        />
        <MetricCard
          title="Risk Score"
          value={kpis.risk_score.toString()}
          icon={Shield}
          status={kpis.risk_score <= 30 ? "good" : kpis.risk_score <= 60 ? "warning" : "critical"}
        />
        <MetricCard
          title="Liquidity Ratio"
          value={`${kpis.liquidity_ratio.toFixed(1)}x`}
          icon={DollarSign}
          status={kpis.liquidity_ratio >= 1.5 ? "good" : kpis.liquidity_ratio >= 1.0 ? "warning" : "critical"}
        />
      </div>

      {/* Alerts with Actions */}
      {alerts && alerts.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--white)' }}>
            Active Alerts
          </h2>
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div key={alert.id} className="flex items-center justify-between rounded-lg p-4"
                   style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
                <div className="flex items-center gap-3">
                  {alert.severity === "critical" ? (
                    <AlertTriangle className="h-5 w-5 text-red-400" />
                  ) : (
                    <CheckCircle2 className="h-5 w-5 text-amber-400" />
                  )}
                  <span className="text-sm" style={{ color: 'var(--light-gray)' }}>
                    {alert.message}
                  </span>
                </div>
                <Button variant="outline" size="sm">
                  {alert.action}
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prioritized Actions Table */}
      {prioritized_actions && prioritized_actions.length > 0 && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Prioritized Actions
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Priority</th>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Agent</th>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Action</th>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Routed To</th>
                </tr>
              </thead>
              <tbody>
                {prioritized_actions.map((action, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <td className="py-2 px-3">
                      <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                        action.priority === 1 ? 'bg-red-500/20 text-red-400' :
                        action.priority === 2 ? 'bg-amber-500/20 text-amber-400' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>
                        {action.priority}
                      </span>
                    </td>
                    <td className="py-2 px-3" style={{ color: 'var(--primary-purple)' }}>{action.agent}</td>
                    <td className="py-2 px-3" style={{ color: 'var(--light-gray)' }}>{action.action}</td>
                    <td className="py-2 px-3" style={{ color: 'var(--medium-gray)' }}>{action.routed_to}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
