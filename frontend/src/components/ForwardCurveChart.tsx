import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ForwardCurve } from "../types";

interface Props {
  current: ForwardCurve;
  historical?: ForwardCurve;
}

interface ChartRow {
  tenor: number;
  currentLabel: string;
  current?: number;
  historicalLabel?: string;
  historical?: number;
}

export default function ForwardCurveChart({ current, historical }: Props) {
  if (current.points.length === 0) return null;

  // Merge data by TENOR for the chart — this aligns "1M forward" across dates
  const tenorMap = new Map<number, ChartRow>();

  for (const pt of current.points) {
    tenorMap.set(pt.tenor, {
      tenor: pt.tenor,
      currentLabel: pt.label,
      current: pt.price,
    });
  }

  if (historical) {
    for (const pt of historical.points) {
      const existing = tenorMap.get(pt.tenor);
      if (existing) {
        existing.historical = pt.price;
        existing.historicalLabel = pt.label;
      } else {
        tenorMap.set(pt.tenor, {
          tenor: pt.tenor,
          currentLabel: `+${pt.tenor}M`,
          historical: pt.price,
          historicalLabel: pt.label,
        });
      }
    }
  }

  // Sort by tenor and limit to first 36 for readability
  const data = [...tenorMap.values()]
    .sort((a, b) => a.tenor - b.tenor)
    .slice(0, 36);

  // Compute Y domain with padding
  const allPrices = data.flatMap((d) =>
    [d.current, d.historical].filter((v): v is number => v != null)
  );
  const minPrice = Math.min(...allPrices);
  const maxPrice = Math.max(...allPrices);
  const padding = (maxPrice - minPrice) * 0.08 || 1;

  return (
    <div className="bg-slate-800/30 rounded-xl p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-sm font-medium text-slate-300">
          Forward Curve — {current.commodity}
        </h2>
        <span className="text-xs text-slate-500">{current.unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="currentLabel"
            tick={{ fill: "#64748b", fontSize: 11 }}
            tickLine={{ stroke: "#334155" }}
            axisLine={{ stroke: "#334155" }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[Math.floor(minPrice - padding), Math.ceil(maxPrice + padding)]}
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
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const row = payload[0].payload as ChartRow;
              return (
                <div style={{
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "8px 12px",
                  fontSize: "13px",
                }}>
                  {row.current != null && (
                    <div style={{ color: "#22c55e" }}>
                      {row.currentLabel}: {row.current.toFixed(2)}
                    </div>
                  )}
                  {row.historical != null && (
                    <div style={{ color: "#f97316" }}>
                      {row.historicalLabel}: {row.historical.toFixed(2)}
                    </div>
                  )}
                  {row.current != null && row.historical != null && (
                    <div style={{ color: "#94a3b8", marginTop: 4, fontSize: "11px" }}>
                      Diff: {(row.current - row.historical) >= 0 ? "+" : ""}
                      {(row.current - row.historical).toFixed(2)}
                    </div>
                  )}
                </div>
              );
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }}
          />
          <Line
            type="monotone"
            dataKey="current"
            name={`Current (${current.as_of})`}
            stroke="#22c55e"
            strokeWidth={2.5}
            dot={{ r: 2.5, fill: "#22c55e" }}
            activeDot={{ r: 5 }}
            connectNulls
          />
          {historical && (
            <Line
              type="monotone"
              dataKey="historical"
              name={`Historical (${historical.as_of})`}
              stroke="#f97316"
              strokeWidth={2}
              strokeDasharray="6 3"
              dot={{ r: 2, fill: "#f97316" }}
              activeDot={{ r: 4 }}
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
