import { useMemo } from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div
        className="rounded-lg p-3 border shadow-lg"
        style={{ backgroundColor: "var(--dark-blue)", borderColor: "var(--purple-dark)" }}
      >
        <p className="text-sm mb-2" style={{ color: "var(--light-gray)" }}>{label}</p>
        {payload.map((entry: any, i: number) => (
          <p key={`tt-${entry.name ?? i}`} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === "number" ? entry.value.toLocaleString() : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const chartColors = {
  primary: "#C1A6FF",
  secondary: "#5F4896",
  success: "#10B981",
  warning: "#FB923C",
  info: "#3B82F6",
  error: "#DC2626",
};

// ─── TrendChart ───────────────────────────────────────────────────────────────

interface TrendChartProps {
  data: Array<{ name: string; value?: number; target?: number; [key: string]: any }>;
  dataKey?: string;
  color?: string;
  height?: number;
  showTarget?: boolean;
}

export function TrendChart({
  data,
  dataKey = "value",
  color = chartColors.primary,
  height = 300,
  showTarget = false,
}: TrendChartProps) {
  const stableData = useMemo(() => data, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={stableData}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(95,72,150,0.2)" />
        <XAxis dataKey="name" stroke="#9EA9B3" style={{ fontSize: "12px" }} />
        <YAxis stroke="#9EA9B3" style={{ fontSize: "12px" }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ color: "#CED4D9" }} />
        <Line
          key={`trendline-${dataKey}`}
          type="monotone"
          dataKey={dataKey}
          name={dataKey}
          stroke={color}
          strokeWidth={3}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
        {showTarget && (
          <Line
            key="trendline-target"
            type="monotone"
            dataKey="target"
            name="Target"
            stroke={chartColors.warning}
            strokeWidth={2}
            strokeDasharray="5 5"
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}

// ─── AreaChartComponent ───────────────────────────────────────────────────────

interface AreaChartComponentProps {
  data: Array<any>;
  areas: Array<{ dataKey: string; name: string; color: string }>;
  height?: number;
  stacked?: boolean;
}

export function AreaChartComponent({
  data,
  areas,
  height = 300,
  stacked = false,
}: AreaChartComponentProps) {
  const stableData = useMemo(() => data, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={stableData}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(95,72,150,0.2)" />
        <XAxis dataKey="name" stroke="#9EA9B3" style={{ fontSize: "12px" }} />
        <YAxis stroke="#9EA9B3" style={{ fontSize: "12px" }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ color: "#CED4D9" }} />
        {areas.map((area) => (
          <Area
            key={`area-${area.dataKey}`}
            type="monotone"
            dataKey={area.dataKey}
            name={area.name}
            stackId={stacked ? "stack" : undefined}
            stroke={area.color}
            fill={area.color}
            fillOpacity={0.6}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ─── BarChartComponent ────────────────────────────────────────────────────────

interface BarChartComponentProps {
  data: Array<any>;
  bars: Array<{ dataKey: string; name: string; color: string }>;
  height?: number;
  horizontal?: boolean;
}

export function BarChartComponent({
  data,
  bars,
  height = 300,
  horizontal = false,
}: BarChartComponentProps) {
  const stableData = useMemo(() => data, [data]);

  const xAxisProps = horizontal
    ? { type: "number" as const }
    : { type: "category" as const, dataKey: "name" };

  const yAxisProps = horizontal
    ? { type: "category" as const, dataKey: "name", width: 120 }
    : { type: "number" as const };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={stableData} layout={horizontal ? "vertical" : "horizontal"}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(95,72,150,0.2)" />
        <XAxis {...xAxisProps} stroke="#9EA9B3" style={{ fontSize: "12px" }} />
        <YAxis {...yAxisProps} stroke="#9EA9B3" style={{ fontSize: "12px" }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ color: "#CED4D9" }} />
        {bars.map((bar) => (
          <Bar
            key={`bar-${bar.dataKey}`}
            dataKey={bar.dataKey}
            name={bar.name}
            fill={bar.color}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

// ─── DonutChart ───────────────────────────────────────────────────────────────

interface DonutChartProps {
  data: Array<{ name: string; value: number; color: string }>;
  height?: number;
}

export function DonutChart({ data, height = 300 }: DonutChartProps) {
  const stableData = useMemo(() => data, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={stableData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
          labelStyle={{ fill: "#CED4D9", fontSize: "12px" }}
        >
          {stableData.map((entry, idx) => (
            <Cell key={`cell-${entry.name}-${idx}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
      </PieChart>
    </ResponsiveContainer>
  );
}

// ─── MultiLineChart ───────────────────────────────────────────────────────────

interface MultiLineChartProps {
  data: Array<any>;
  lines: Array<{ dataKey: string; name: string; color: string }>;
  height?: number;
}

export function MultiLineChart({ data, lines, height = 300 }: MultiLineChartProps) {
  const stableData = useMemo(() => data, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={stableData}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(95,72,150,0.2)" />
        <XAxis dataKey="name" stroke="#9EA9B3" style={{ fontSize: "12px" }} />
        <YAxis stroke="#9EA9B3" style={{ fontSize: "12px" }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ color: "#CED4D9" }} />
        {lines.map((line) => (
          <Line
            key={`multiline-${line.dataKey}`}
            type="monotone"
            dataKey={line.dataKey}
            name={line.name}
            stroke={line.color}
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
