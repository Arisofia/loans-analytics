import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon?: LucideIcon;
  status?: "normal" | "warning" | "critical" | "not-configured";
  subtitle?: string;
}

const statusConfig = {
  normal: { emoji: "✅", color: "var(--success)" },
  warning: { emoji: "⚠️", color: "var(--warning)" },
  critical: { emoji: "🔴", color: "var(--error)" },
  "not-configured": { emoji: "⊙", color: "var(--medium-gray)" },
};

export function MetricCard({
  title,
  value,
  change,
  changeType = "neutral",
  icon: Icon,
  status,
  subtitle,
}: MetricCardProps) {
  const statusInfo = status ? statusConfig[status] : null;

  return (
    <div
      className="rounded-lg p-5 border relative overflow-hidden"
      style={{
        background: "var(--gradient-card-primary)",
        borderColor: "var(--purple-dark)",
        borderRadius: "var(--card-border-radius)",
      }}
    >
      {Icon && (
        <div className="absolute top-4 right-4 opacity-20">
          <Icon className="h-8 w-8" style={{ color: "var(--primary-purple)" }} />
        </div>
      )}

      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm uppercase tracking-wide" style={{ color: "var(--light-gray)" }}>
          {title}
        </h3>
        {statusInfo && (
          <span className="text-lg" title={status}>
            {statusInfo.emoji}
          </span>
        )}
      </div>

      <div className="mb-1">
        <p
          className="font-bold tracking-tight"
          style={{
            fontSize: "var(--text-metric)",
            color: "var(--white)",
            fontFamily: "var(--font-secondary)",
          }}
        >
          {value}
        </p>
      </div>

      {(subtitle || change) && (
        <div className="flex items-center gap-2">
          {change && (
            <span
              className="text-sm font-semibold"
              style={{
                color:
                  changeType === "positive"
                    ? "var(--success)"
                    : changeType === "negative"
                    ? "var(--error)"
                    : "var(--medium-gray)",
              }}
            >
              {change}
            </span>
          )}
          {subtitle && (
            <span className="text-xs" style={{ color: "var(--dark-gray)" }}>
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

interface AlertCardProps {
  type: "critical" | "warning" | "info";
  title: string;
  message: string;
  timestamp?: string;
  actions?: ReactNode;
}

export function AlertCard({ type, title, message, timestamp, actions }: AlertCardProps) {
  const typeConfig = {
    critical: { borderColor: "var(--error)", bgColor: "rgba(220, 38, 38, 0.08)" },
    warning: { borderColor: "var(--warning)", bgColor: "rgba(251, 146, 60, 0.08)" },
    info: { borderColor: "var(--info)", bgColor: "rgba(59, 130, 246, 0.08)" },
  };

  const config = typeConfig[type];

  return (
    <div
      className="rounded-lg p-4 border-l-4"
      style={{
        backgroundColor: config.bgColor,
        borderLeftColor: config.borderColor,
      }}
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-semibold" style={{ color: "var(--white)" }}>
          {title}
        </h4>
        {timestamp && (
          <span className="text-xs" style={{ color: "var(--dark-gray)" }}>
            {timestamp}
          </span>
        )}
      </div>
      <p className="text-sm mb-3" style={{ color: "var(--light-gray)" }}>
        {message}
      </p>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}

interface ConfidenceBadgeProps {
  level: "high" | "medium" | "low";
}

export function ConfidenceBadge({ level }: ConfidenceBadgeProps) {
  const config = {
    high: { emoji: "🟢", label: "High Confidence", color: "var(--success)" },
    medium: { emoji: "🟡", label: "Medium Confidence", color: "var(--warning)" },
    low: { emoji: "🔴", label: "Low Confidence", color: "var(--error)" },
  };

  const { emoji, label, color } = config[level];

  return (
    <span
      className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold"
      style={{
        backgroundColor: `${color}20`,
        color: color,
        border: `1px solid ${color}40`,
      }}
    >
      <span>{emoji}</span>
      <span>{label}</span>
    </span>
  );
}
