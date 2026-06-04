import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { HistoryData, ForecastData, SignalPoint } from "../lib/api";

interface Props {
  history: HistoryData;
  forecast: ForecastData | null;
  currentYear: number;
}

const SIGNALS = [
  { key: "ndvi" as const, label: "NDVI", unit: "", color: "#22d3ee" },
  { key: "nighttime_lights" as const, label: "Night Lights", unit: " DN", color: "#fbbf24" },
  { key: "land_surface_temp" as const, label: "Land Surface Temp", unit: "°C", color: "#f87171" },
  { key: "built_up_extent" as const, label: "Built-up", unit: " m²", color: "#a78bfa" },
];

function merge(hist: SignalPoint[], fore: SignalPoint[] | undefined): { year: number; value: number | null; lower?: number; upper?: number; future: boolean }[] {
  const histPoints = hist.map((p) => ({ ...p, future: false }));
  const forePoints = (fore ?? []).map((p) => ({ ...p, future: true }));
  return [...histPoints, ...forePoints];
}

function SignalChart({
  label,
  data,
  unit,
  color,
  currentYear,
}: {
  label: string;
  data: ReturnType<typeof merge>;
  unit: string;
  color: string;
  currentYear: number;
}) {
  const valid = data.filter((d) => d.value !== null);
  const values = valid.map((d) => d.value as number);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const pad = (max - min) * 0.15 || 1;

  return (
    <div className="mb-4">
      <div className="text-xs text-slate-400 mb-1 font-medium">{label}</div>
      <ResponsiveContainer width="100%" height={80}>
        <ComposedChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <XAxis dataKey="year" tick={{ fontSize: 9, fill: "#64748b" }} tickLine={false} axisLine={false} interval={9} />
          <YAxis domain={[min - pad, max + pad]} tick={{ fontSize: 9, fill: "#64748b" }} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ background: "#1a1d2e", border: "1px solid #2a2d3e", borderRadius: 4, fontSize: 11 }}
            formatter={(v: number) => [`${v?.toFixed(2)}${unit}`, label]}
            labelFormatter={(y) => `Year: ${y}`}
          />
          <ReferenceLine x={2025} stroke="#4f8ef7" strokeDasharray="3 3" strokeWidth={1} />
          <ReferenceLine x={currentYear} stroke={currentYear > 2025 ? "#a855f7" : "#22d3ee"} strokeWidth={1.5} />
          {data.some((d) => d.lower !== undefined) && (
            <Area
              dataKey="upper"
              stroke="none"
              fill={color}
              fillOpacity={0.1}
              isAnimationActive={false}
            />
          )}
          <Line
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function SignalCharts({ history, forecast, currentYear }: Props) {
  return (
    <div className="px-4 py-3 border-b border-chronos-border">
      {SIGNALS.map(({ key, label, unit, color }) => {
        const foreSignals = forecast?.signals[key];
        const merged = merge(history[key], foreSignals);
        return (
          <SignalChart
            key={key}
            label={label}
            data={merged}
            unit={unit}
            color={color}
            currentYear={currentYear}
          />
        );
      })}
    </div>
  );
}
