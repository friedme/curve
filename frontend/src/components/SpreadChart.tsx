import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { SpreadPoint } from "../types";

interface Props {
  spread: SpreadPoint[];
  unit: string;
}

export default function SpreadChart({ spread, unit }: Props) {
  if (spread.length === 0) return null;

  return (
    <div className="bg-slate-800/30 rounded-xl p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-sm font-medium text-slate-300">
          Spread (Current minus Historical)
        </h2>
        <span className="text-xs text-slate-500">{unit}</span>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={spread} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="current_label"
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
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "8px",
              fontSize: "13px",
            }}
            labelStyle={{ color: "#94a3b8" }}
            formatter={(value: unknown) => {
              const v = Number(value);
              return [`${v >= 0 ? "+" : ""}${v.toFixed(2)}`, "Spread"];
            }}
          />
          <Bar dataKey="diff" radius={[3, 3, 0, 0]}>
            {spread.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.diff >= 0 ? "#22c55e" : "#ef4444"}
                fillOpacity={0.7}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
