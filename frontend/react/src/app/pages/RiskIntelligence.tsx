import { useSection } from "@/hooks/useData";
import { MetricCard, AlertCard } from "../components/MetricComponents";
import { MultiLineChart } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { AlertTriangle, TrendingDown, Shield, Percent } from "lucide-react";

interface RiskData {
  metrics: {
    par30: number;
    par60: number;
    par90: number;
    expected_loss: number;
  };
  risk_alerts: Array<{
    id: string;
    message: string;
    severity: string;
  }>;
  delinquency_trend: Array<{
    month: string;
    par30: number;
    par60: number;
    par90: number;
  }>;
}

export default function RiskIntelligence() {
  const { data, loading, error, refetch } = useSection<RiskData>("risk");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { metrics, risk_alerts, delinquency_trend } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div>
        <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Risk Intelligence
        </h1>
        <p style={{ color: 'var(--medium-gray)' }}>
          Portfolio risk monitoring and early warning system
        </p>
      </div>

      {/* PAR Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="PAR 30"
          value={`${metrics.par30.toFixed(1)}%`}
          icon={AlertTriangle}
          status={metrics.par30 >= 8 ? "critical" : metrics.par30 >= 5 ? "warning" : "good"}
        />
        <MetricCard
          title="PAR 60"
          value={`${metrics.par60.toFixed(1)}%`}
          icon={TrendingDown}
          status={metrics.par60 > 5 ? "critical" : metrics.par60 > 3 ? "warning" : "good"}
        />
        <MetricCard
          title="PAR 90"
          value={`${metrics.par90.toFixed(1)}%`}
          icon={Shield}
          status={metrics.par90 > 3 ? "critical" : metrics.par90 > 1.5 ? "warning" : "good"}
        />
        <MetricCard
          title="Expected Loss"
          value={`${metrics.expected_loss.toFixed(2)}%`}
          icon={Percent}
          status={metrics.expected_loss > 5 ? "critical" : metrics.expected_loss > 2 ? "warning" : "good"}
        />
      </div>

      {/* Risk Alerts */}
      {risk_alerts && risk_alerts.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--white)' }}>
            Risk Alerts
          </h2>
          <div className="space-y-2">
            {risk_alerts.map((alert) => (
              <AlertCard
                key={alert.id}
                type={alert.severity as "critical" | "warning" | "info"}
                message={alert.message}
              />
            ))}
          </div>
        </div>
      )}

      {/* Delinquency Trend */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          Delinquency Trend
        </h3>
        <MultiLineChart
          data={delinquency_trend}
          xKey="month"
          lines={[
            { dataKey: "par30", name: "PAR 30", color: "#f59e0b" },
            { dataKey: "par60", name: "PAR 60", color: "#f97316" },
            { dataKey: "par90", name: "PAR 90", color: "#ef4444" },
          ]}
          height={320}
        />
      </div>
    </div>
  );
}
