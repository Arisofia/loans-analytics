import { useSection } from "@/hooks/useData";
import { MetricCard } from "../components/MetricComponents";
import { TrendChart, BarChartComponent } from "../components/Charts";
import { LoadingState, ErrorState } from "../components/LoadingState";
import { DollarSign, Users, Percent, TrendingUp } from "lucide-react";

interface UnitEconomicsData {
  customer_economics: {
    ltv: number;
    cac: number;
    ltv_cac_ratio: number;
    payback_period: number;
  };
  profitability: {
    nim: number;
    cost_of_risk: number;
    roa: number;
    roe: number;
  };
  reconciliation: Array<{
    item: string;
    calculated: number;
    reported: number;
    variance: number;
    status: string;
  }>;
  gross_margin_trend: Array<{
    month: string;
    margin: number;
  }>;
  ticket_segmentation: Array<{
    band: string;
    count: number;
    amount: number;
    default_rate: number;
  }>;
}

export default function UnitEconomics() {
  const { data, loading, error, refetch } = useSection<UnitEconomicsData>("unit-economics");

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;
  if (!data) return null;

  const { customer_economics, profitability, reconciliation, gross_margin_trend, ticket_segmentation } = data;

  return (
    <div className="p-6 space-y-6 pb-24 md:pb-6">
      {/* Header */}
      <div>
        <h1 style={{ background: 'var(--gradient-title)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Unit Economics
        </h1>
        <p style={{ color: 'var(--medium-gray)' }}>
          Customer lifetime value, profitability, and economic sustainability
        </p>
      </div>

      {/* Customer Economics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="LTV"
          value={`$${customer_economics.ltv.toLocaleString()}`}
          icon={DollarSign}
          status="neutral"
        />
        <MetricCard
          title="CAC"
          value={`$${customer_economics.cac.toFixed(0)}`}
          icon={Users}
          status="neutral"
        />
        <MetricCard
          title="LTV/CAC"
          value={`${customer_economics.ltv_cac_ratio.toFixed(1)}x`}
          icon={TrendingUp}
          status={customer_economics.ltv_cac_ratio >= 3 ? "good" : customer_economics.ltv_cac_ratio >= 2 ? "warning" : "critical"}
        />
        <MetricCard
          title="Payback Period"
          value={`${customer_economics.payback_period} mo`}
          icon={Percent}
          status={customer_economics.payback_period <= 6 ? "good" : customer_economics.payback_period <= 12 ? "warning" : "critical"}
        />
      </div>

      {/* Profitability Metrics */}
      <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
        <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
          Profitability Metrics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-main)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--medium-gray)' }}>NIM</p>
            <p className="text-lg font-bold" style={{ color: 'var(--primary-purple)' }}>
              {profitability.nim.toFixed(1)}%
            </p>
          </div>
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-main)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--medium-gray)' }}>Cost of Risk</p>
            <p className="text-lg font-bold" style={{ color: profitability.cost_of_risk > 5 ? '#ef4444' : '#a78bfa' }}>
              {profitability.cost_of_risk.toFixed(2)}%
            </p>
          </div>
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-main)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--medium-gray)' }}>ROA</p>
            <p className="text-lg font-bold" style={{ color: 'var(--primary-purple)' }}>
              {profitability.roa.toFixed(2)}%
            </p>
          </div>
          <div className="text-center p-3 rounded-lg" style={{ backgroundColor: 'var(--bg-main)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--medium-gray)' }}>ROE</p>
            <p className="text-lg font-bold" style={{ color: 'var(--primary-purple)' }}>
              {profitability.roe.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Reconciliation Grid */}
      {reconciliation && reconciliation.length > 0 && (
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Reconciliation
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                  <th className="text-left py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Item</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Calculated</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Reported</th>
                  <th className="text-right py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Variance</th>
                  <th className="text-center py-2 px-3 font-semibold" style={{ color: 'var(--medium-gray)' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {reconciliation.map((row) => (
                  <tr key={row.item} style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <td className="py-2 px-3" style={{ color: 'var(--white)' }}>{row.item}</td>
                    <td className="py-2 px-3 text-right" style={{ color: 'var(--light-gray)' }}>
                      ${row.calculated.toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-right" style={{ color: 'var(--light-gray)' }}>
                      ${row.reported.toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className={Math.abs(row.variance) > 5 ? 'text-red-400' : 'text-emerald-400'}>
                        {row.variance > 0 ? '+' : ''}{row.variance.toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        row.status === 'OK' ? 'bg-emerald-500/20 text-emerald-400' :
                        row.status === 'WARNING' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs mt-3" style={{ color: 'var(--medium-gray)' }}>
            ⚠️ Variances above 5% require investigation per GOVERNANCE policy
          </p>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Gross Margin Trend */}
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Gross Margin Trend
          </h3>
          <TrendChart
            data={gross_margin_trend}
            xKey="month"
            yKey="margin"
            height={250}
          />
        </div>

        {/* Ticket Segmentation */}
        <div className="rounded-xl p-5" style={{ backgroundColor: 'var(--card-bg)', border: '1px solid var(--card-border)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--white)' }}>
            Ticket Segmentation
          </h3>
          <BarChartComponent
            data={ticket_segmentation}
            xKey="band"
            yKey="count"
            height={250}
          />
          {ticket_segmentation && (
            <div className="overflow-x-auto mt-4">
              <table className="w-full text-xs">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <th className="text-left py-1 px-2" style={{ color: 'var(--medium-gray)' }}>Band</th>
                    <th className="text-right py-1 px-2" style={{ color: 'var(--medium-gray)' }}>Count</th>
                    <th className="text-right py-1 px-2" style={{ color: 'var(--medium-gray)' }}>Amount</th>
                    <th className="text-right py-1 px-2" style={{ color: 'var(--medium-gray)' }}>Default %</th>
                  </tr>
                </thead>
                <tbody>
                  {ticket_segmentation.map((row) => (
                    <tr key={row.band} style={{ borderBottom: '1px solid var(--card-border)' }}>
                      <td className="py-1 px-2" style={{ color: 'var(--white)' }}>{row.band}</td>
                      <td className="py-1 px-2 text-right" style={{ color: 'var(--light-gray)' }}>{row.count}</td>
                      <td className="py-1 px-2 text-right" style={{ color: 'var(--light-gray)' }}>
                        ${(row.amount / 1e3).toFixed(0)}K
                      </td>
                      <td className="py-1 px-2 text-right">
                        <span className={row.default_rate > 5 ? 'text-red-400' : 'text-emerald-400'}>
                          {row.default_rate.toFixed(2)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
