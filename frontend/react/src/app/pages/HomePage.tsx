import { useSection } from "@/hooks/useData";
import { MetricCard, AlertCard } from "../components/MetricComponents";
import { TrendChart, DonutChart } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Button } from "@/components/ui/button";
import {
  DollarSign,
  Users,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Percent,
  BarChart3,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router";

interface SummaryData {
  kpis: {
    total_outstanding: number;
    active_loans: number;
    par30: number;
    default_rate: number;
    collection_rate: number;
    active_borrowers: number;
  };
  alerts: Array<{
    id: string;
    type: string;
    message: string;
    severity: string;
    timestamp: string;
  }>;
  cashflow_trend: Array<{
    month: string;
    inflow: number;
    outflow: number;
  }>;
  portfolio_mix: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  health_summary: {
    credit_quality: string;
    liquidity: string;
    profitability: string;
    growth: string;
  };
}

export default function HomePage() {
  const { data, loading, error, refetch } = useSection<SummaryData>("summary");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { kpis, alerts, cashflow_trend, portfolio_mix, health_summary } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Dashboard
          </h1>
          <p style={{ color: 'var(--medium-gray)' }}>
            Real-time portfolio intelligence
          </p>
        </div>
        <div className="hidden md:flex gap-2">
          <Button variant="outline" size="sm">Export</Button>
          <Button size="sm">Refresh</Button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard
          title="Outstanding Loans"
          value={`$${(kpis.total_outstanding / 1e6).toFixed(1)}M`}
          icon={DollarSign}
          status="neutral"
        />
        <MetricCard
          title="Active Loans"
          value={kpis.active_loans.toLocaleString()}
          icon={BarChart3}
          status="good"
        />
        <MetricCard
          title="PAR30"
          value={`${kpis.par30.toFixed(1)}%`}
          icon={AlertTriangle}
          status={kpis.par30 > 10 ? "critical" : kpis.par30 > 5 ? "warning" : "good"}
        />
        <MetricCard
          title="Default Rate"
          value={`${kpis.default_rate.toFixed(2)}%`}
          icon={TrendingDown}
          status={kpis.default_rate > 5 ? "critical" : kpis.default_rate > 3 ? "warning" : "good"}
        />
        <MetricCard
          title="Collection Rate"
          value={`${kpis.collection_rate.toFixed(1)}%`}
          icon={Percent}
          status={kpis.collection_rate >= 95 ? "good" : kpis.collection_rate >= 85 ? "warning" : "critical"}
        />
        <MetricCard
          title="Active Borrowers"
          value={kpis.active_borrowers.toLocaleString()}
          icon={Users}
          status="neutral"
        />
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3 flex-wrap">
        <Link to="/executive">
          <Button variant="outline" size="sm" className="gap-2">
            <TrendingUp className="h-4 w-4" /> Executive View <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
        <Link to="/risk">
          <Button variant="outline" size="sm" className="gap-2">
            <AlertTriangle className="h-4 w-4" /> Risk Intelligence <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
        <Link to="/collections">
          <Button variant="outline" size="sm" className="gap-2">
            <Users className="h-4 w-4" /> Collections <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>

      {/* Alerts */}
      {alerts && alerts.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--white)' }}>Active Alerts</h2>
          <div className="space-y-2">
            {alerts.map((alert) => (
              <AlertCard
                key={alert.id}
                type={alert.severity as "critical" | "warning" | "info"}
                message={alert.message}
              />
            ))}
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Cashflow Trend */}
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Cashflow Trend
          </h3>
          <TrendChart
            data={cashflow_trend}
            xKey="month"
            yKey="inflow"
            height={220}
          />
        </div>

        {/* Portfolio Mix */}
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Portfolio Mix
          </h3>
          <DonutChart data={portfolio_mix} height={220} />
        </div>
      </div>

      {/* Health Summary */}
      {health_summary && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Portfolio Health Summary
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(health_summary).map(([key, value]) => (
              <div key={key} className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-main)' }}>
                <p className="text-xs capitalize mb-1" style={{ color: 'var(--medium-gray)' }}>
                  {key.replace(/_/g, ' ')}
                </p>
                <p className={`text-sm font-bold ${
                  value === 'Good' || value === 'Strong' ? 'text-emerald-400' :
                  value === 'Fair' || value === 'Moderate' ? 'text-amber-400' :
                  'text-red-400'
                }`}>
                  {value}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
