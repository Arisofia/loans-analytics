import { useSection } from "@/hooks/useData";
import { MetricCard, AlertCard } from "../components/MetricComponents";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { Building2, ShieldCheck, Wallet, BarChart3 } from "lucide-react";

interface InvestorData {
  covenants: {
    compliance_status: string;
    covenants: Array<{
      name: string;
      current: number;
      threshold: number;
      status: string;
      description: string;
    }>;
  };
  holding_indicators?: {
    liquidity: {
      reserve_ratio_pct: number;
      is_adequate: boolean;
    };
    reconciliation: {
      reconciled: boolean;
      unit_ec_default_rate_pct: number;
    };
  };
  scenarios?: Array<{
    name: string;
    impact: Record<string, number>;
  }>;
}

export default function InvestorRoom() {
  const { data, loading, error, refetch } = useSection<InvestorData>("investor");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { covenants, holding_indicators, scenarios } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div>
        <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Investor Room
        </h1>
        <p style={{ color: 'var(--medium-gray)' }}>
          Institutional financial intelligence and compliance
        </p>
      </div>

      {/* Compliance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Covenant Status"
          value={covenants.compliance_status}
          icon={ShieldCheck}
          status={covenants.compliance_status === "COMPLIANT" ? "good" : "critical"}
        />
        {holding_indicators && (
          <>
            <MetricCard
              title="Liquidity Reserve"
              value={`${holding_indicators.liquidity.reserve_ratio_pct.toFixed(2)}%`}
              icon={Wallet}
              status={holding_indicators.liquidity.is_adequate ? "good" : "warning"}
            />
            <MetricCard
              title="Reconciliation"
              value={holding_indicators.reconciliation.reconciled ? "Verified" : "Discrepancy"}
              icon={BarChart3}
              status={holding_indicators.reconciliation.reconciled ? "good" : "warning"}
            />
          </>
        )}
        <MetricCard
          title="Reporting Entity"
          value="ÁBACO Holding"
          icon={Building2}
          status="neutral"
        />
      </div>

      {/* Covenant Details */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          Debt Covenant Monitoring
        </h3>
        <div className="space-y-4">
          {covenants.covenants.map((cov, idx) => (
            <div key={idx} className="flex flex-col space-y-2 border-b border-gray-800 pb-3 last:border-0">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium" style={{ color: 'var(--light-gray)' }}>{cov.name}</span>
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                  cov.status === "PASS" ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
                }`}>
                  {cov.status}
                </span>
              </div>
              <p className="text-xs text-gray-500">{cov.description}</p>
              <div className="flex gap-4 text-xs">
                <span style={{ color: 'var(--medium-gray)' }}>Current: <span style={{ color: 'var(--white)' }}>{cov.current}%</span></span>
                <span style={{ color: 'var(--medium-gray)' }}>Threshold: <span style={{ color: 'var(--white)' }}>{cov.threshold}%</span></span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Scenario Projections */}
      {scenarios && scenarios.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold" style={{ color: 'var(--white)' }}>
            Scenario Projections
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scenarios.map((sc, idx) => (
              <div key={idx} className="rounded-xl p-4" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
                <h4 className="text-xs font-bold uppercase tracking-wider mb-3" style={{ color: 'var(--primary-purple)' }}>
                  {sc.name}
                </h4>
                <div className="space-y-2">
                  {Object.entries(sc.impact).map(([metric, value]) => (
                    <div key={metric} className="flex justify-between text-xs">
                      <span style={{ color: 'var(--medium-gray)' }}>{metric}</span>
                      <span style={{ color: 'var(--white)' }}>{typeof value === 'number' ? value.toFixed(2) : value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
