import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { SpotPrice } from "../types";
import { useSpotHistory } from "../hooks/useCurveData";

interface Props {
  prices: SpotPrice[];
}

const PERIODS = ["3mo", "6mo", "1y", "2y", "5y"] as const;

export default function SpotPrices({ prices }: Props) {
  const [selectedSlug, setSelectedSlug] = useState<string | null>(prices[0]?.slug ?? null);
  const [period, setPeriod] = useState("1y");
  const { data: history, isLoading } = useSpotHistory(selectedSlug, period);

  if (prices.length === 0) return null;

  const selected = prices.find((p) => p.slug === selectedSlug);

  return (
    <div className="mt-8 border-t border-slate-800 pt-6">
      <h2 className="text-sm font-medium text-slate-400 mb-3">Spot Prices</h2>
      <div className="grid grid-cols-4 gap-3">
        {prices.map((p) => (
          <button
            key={p.slug}
            onClick={() =>
              setSelectedSlug(selectedSlug === p.slug ? null : p.slug)
            }
            className={`text-left rounded-lg px-4 py-3 transition-colors ${
              selectedSlug === p.slug
                ? "bg-slate-700/50 ring-1 ring-emerald-500/40"
                : "bg-slate-800/30 hover:bg-slate-800/60"
            }`}
          >
            <div className="text-xs text-slate-500 mb-1">{p.display_name}</div>
            <div className="text-lg font-semibold text-slate-100">
              {formatPrice(p.price, p.unit)}
            </div>
            <div className="text-xs text-slate-600 mt-0.5">
              {p.contract} &middot; {p.unit}
            </div>
          </button>
        ))}
      </div>

      {/* History chart */}
      {selectedSlug && (
        <div className="mt-4 bg-slate-800/30 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-slate-300">
              {selected?.display_name} — Price History
              {history?.history_label && (
                <span className="ml-2 text-xs text-slate-500 font-normal">
                  ({history.history_label})
                </span>
              )}
            </h3>
            <div className="flex gap-1">
              {PERIODS.map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                    period === p
                      ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40"
                      : "bg-slate-800/50 text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {isLoading && (
            <div className="flex items-center gap-2 text-slate-500 text-sm py-8 justify-center">
              <div className="w-4 h-4 border-2 border-slate-600 border-t-slate-300 rounded-full animate-spin" />
              Loading history...
            </div>
          )}

          {history && history.points.length > 0 && !isLoading && (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart
                data={history.points}
                margin={{ top: 5, right: 20, bottom: 5, left: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  tickLine={{ stroke: "#334155" }}
                  axisLine={{ stroke: "#334155" }}
                  tickFormatter={(d: string) => {
                    const dt = new Date(d);
                    return dt.toLocaleDateString("en-US", {
                      month: "short",
                      year: "2-digit",
                    });
                  }}
                  interval="preserveStartEnd"
                  minTickGap={60}
                />
                <YAxis
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  tickLine={{ stroke: "#334155" }}
                  axisLine={{ stroke: "#334155" }}
                  width={70}
                  domain={["auto", "auto"]}
                  tickFormatter={(v: number) => v.toLocaleString()}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    fontSize: "13px",
                  }}
                  labelStyle={{ color: "#94a3b8" }}
                  formatter={(value: number) => [
                    formatPrice(value, history.unit),
                    history.display_name,
                  ]}
                  labelFormatter={(d: string) =>
                    new Date(d).toLocaleDateString("en-US", {
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })
                  }
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#22c55e"
                  strokeWidth={1.5}
                  dot={false}
                  activeDot={{ r: 4, fill: "#22c55e" }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}

          {history && history.points.length === 0 && !isLoading && (
            <div className="text-sm text-slate-500 py-8 text-center">
              No historical data available for this period.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function formatPrice(price: number, unit: string): string {
  if (unit.startsWith("USD")) {
    return `$${price.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
  if (unit.startsWith("EUR")) {
    return `€${price.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
  return price.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
