import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { CurveEvolution, SpreadHistory } from "../types";

const CURVE_COLORS = [
  "#22c55e", // current – green
  "#f97316", // 1W – orange
  "#3b82f6", // 1M – blue
  "#a78bfa", // 3M – purple
  "#64748b", // 6M – slate
  "#ef4444", // 1Y – red
];

// ── Curve Evolution (multi-date overlay) ─────────────────────────

interface EvolutionProps {
  data: CurveEvolution;
}

export function CurveEvolutionChart({ data }: EvolutionProps) {
  const defaultLabels = new Set(["Current", "1M ago"]);
  const [enabled, setEnabled] = useState<Set<string>>(
    () => new Set(data.curves.filter((c) => defaultLabels.has(c.label)).map((c) => c.label))
  );

  // Reset enabled set when curves change (new commodity or data refresh)
  useEffect(() => {
    setEnabled(new Set(data.curves.filter((c) => defaultLabels.has(c.label)).map((c) => c.label)));
  }, [data]);

  if (data.curves.length === 0) return null;

  const toggle = (label: string) => {
    setEnabled((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        // Don't allow deselecting "Current"
        if (label === "Current") return prev;
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  };

  const visibleCurves = data.curves.filter((c) => enabled.has(c.label));
  if (visibleCurves.length === 0) return null;

  // Build rows keyed by tenor, with a column per dated curve
  const tenorMap = new Map<number, Record<string, number | string>>();
  for (const curve of visibleCurves) {
    for (const pt of curve.points) {
      if (!tenorMap.has(pt.tenor)) {
        tenorMap.set(pt.tenor, { tenor: pt.tenor, label: pt.label });
      }
      tenorMap.get(pt.tenor)![curve.label] = pt.price;
    }
  }

  const rows = [...tenorMap.values()]
    .sort((a, b) => (a.tenor as number) - (b.tenor as number))
    .slice(0, 36);

  // Y-axis domain from visible curves only
  const allPrices = rows.flatMap((r) =>
    visibleCurves
      .map((c) => r[c.label])
      .filter((v): v is number => typeof v === "number")
  );
  const min = Math.min(...allPrices);
  const max = Math.max(...allPrices);
  const pad = (max - min) * 0.08 || 1;

  return (
    <div className="bg-slate-800/30 rounded-xl p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-sm font-medium text-slate-300">
          Forward Curve — {data.commodity}
        </h2>
        <span className="text-xs text-slate-500">{data.unit}</span>
      </div>

      {/* Toggle buttons */}
      <div className="flex flex-wrap gap-2 mb-3">
        {data.curves.map((curve, i) => {
          const active = enabled.has(curve.label);
          const color = CURVE_COLORS[i % CURVE_COLORS.length];
          return (
            <button
              key={curve.label}
              onClick={() => toggle(curve.label)}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-all"
              style={{
                backgroundColor: active ? `${color}18` : "#1e293b",
                border: `1px solid ${active ? color : "#334155"}`,
                color: active ? color : "#475569",
                opacity: active ? 1 : 0.5,
              }}
            >
              <span
                className="w-2.5 h-0.5 rounded-full inline-block"
                style={{
                  backgroundColor: color,
                  opacity: active ? 1 : 0.3,
                }}
              />
              {curve.label}
              <span className="text-slate-600" style={{ color: active ? `${color}99` : undefined }}>
                {curve.as_of}
              </span>
            </button>
          );
        })}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={rows} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="label"
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={{ stroke: "#334155" }}
            axisLine={{ stroke: "#334155" }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[Math.floor(min - pad), Math.ceil(max + pad)]}
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={{ stroke: "#334155" }}
            axisLine={{ stroke: "#334155" }}
            width={60}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "8px",
              fontSize: "13px",
            }}
            labelStyle={{ color: "#94a3b8" }}
            formatter={(value: unknown, name: unknown) => [
              Number(value).toFixed(2),
              String(name),
            ]}
          />
          {visibleCurves.map((curve) => {
            const colorIdx = data.curves.indexOf(curve);
            return (
              <Line
                key={curve.label}
                type="monotone"
                dataKey={curve.label}
                name={`${curve.label} (${curve.as_of})`}
                stroke={CURVE_COLORS[colorIdx % CURVE_COLORS.length]}
                strokeWidth={colorIdx === 0 ? 2.5 : 1.5}
                strokeDasharray={colorIdx === 0 ? undefined : "6 3"}
                dot={{ r: colorIdx === 0 ? 2.5 : 1.5, fill: CURVE_COLORS[colorIdx % CURVE_COLORS.length] }}
                activeDot={{ r: colorIdx === 0 ? 5 : 3 }}
                connectNulls
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Calendar Spread Time Series ──────────────────────────────────

interface SpreadProps {
  data: SpreadHistory;
}

export function SpreadTimeSeriesChart({ data }: SpreadProps) {
  if (data.points.length === 0) return null;

  const hasM6 = data.points.some((p) => p.m1_m6 !== null);
  const hasM12 = data.points.some((p) => p.m1_m12 !== null);
  if (!hasM6 && !hasM12) return null;

  return (
    <div className="bg-slate-800/30 rounded-xl p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-sm font-medium text-slate-300">
          Calendar Spreads Over Time — {data.commodity}
        </h2>
        <span className="text-xs text-slate-500">{data.unit}</span>
      </div>
      <p className="text-xs text-slate-500 mb-3">
        Positive = contango (back months priced higher than front)
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data.points} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={{ stroke: "#334155" }}
            axisLine={{ stroke: "#334155" }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={{ stroke: "#334155" }}
            axisLine={{ stroke: "#334155" }}
            width={60}
          />
          <ReferenceLine y={0} stroke="#334155" strokeDasharray="3 3" />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "8px",
              fontSize: "13px",
            }}
            labelStyle={{ color: "#94a3b8" }}
            formatter={(value: unknown, name: unknown) => {
              const v = Number(value);
              return [`${v >= 0 ? "+" : ""}${v.toFixed(2)}`, String(name)];
            }}
          />
          <Legend wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }} />
          {hasM6 && (
            <Line
              type="monotone"
              dataKey="m1_m6"
              name="M1–M6 Spread"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 2, fill: "#3b82f6" }}
              activeDot={{ r: 4 }}
              connectNulls
            />
          )}
          {hasM12 && (
            <Line
              type="monotone"
              dataKey="m1_m12"
              name="M1–M12 Spread"
              stroke="#22c55e"
              strokeWidth={2}
              dot={{ r: 2, fill: "#22c55e" }}
              activeDot={{ r: 4 }}
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
