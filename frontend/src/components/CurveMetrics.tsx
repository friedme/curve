import type { ForwardCurve } from "../types";
import { formatPrice } from "../utils/curveUtils";

interface Props {
  current: ForwardCurve;
  historical?: ForwardCurve;
}

export default function CurveMetrics({ current, historical }: Props) {
  if (current.points.length === 0) return null;

  const front = current.points[0];
  const back = current.points[current.points.length - 1];
  const spread12m = current.points.length >= 12
    ? current.points[11].price - current.points[0].price
    : back.price - front.price;

  const historicalFront = historical?.points?.[0];
  const frontChange = historicalFront
    ? ((front.price - historicalFront.price) / historicalFront.price) * 100
    : null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      <MetricCard
        label="Front Month"
        value={formatPrice(front.price, current.unit)}
        sub={front.label}
      />
      <MetricCard
        label={current.points.length >= 12 ? "12M Spread" : "Front-Back Spread"}
        value={formatPrice(spread12m, current.unit)}
        sub={spread12m > 0 ? "Contango" : spread12m < 0 ? "Backwardation" : "Flat"}
        valueColor={spread12m > 0 ? "#22c55e" : spread12m < 0 ? "#f97316" : "#94a3b8"}
      />
      {frontChange !== null ? (
        <MetricCard
          label="Front vs Historical"
          value={`${frontChange >= 0 ? "+" : ""}${frontChange.toFixed(1)}%`}
          sub={`was ${formatPrice(historicalFront!.price, current.unit)}`}
          valueColor={frontChange >= 0 ? "#22c55e" : "#ef4444"}
        />
      ) : (
        <MetricCard
          label="Back Month"
          value={formatPrice(back.price, current.unit)}
          sub={back.label}
        />
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  sub,
  valueColor,
}: {
  label: string;
  value: string;
  sub?: string;
  valueColor?: string;
}) {
  return (
    <div className="bg-slate-800/50 rounded-lg px-4 py-3">
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className="text-lg font-semibold" style={valueColor ? { color: valueColor } : undefined}>
        {value}
      </div>
      {sub && <div className="text-xs text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}
