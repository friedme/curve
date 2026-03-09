import type { ForwardCurve } from "../types";

interface Props {
  curve: ForwardCurve;
}

export default function DataQualityBanner({ curve }: Props) {
  if (curve.data_quality === "full") return null;

  if (curve.data_quality === "unavailable") {
    return (
      <div className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3 text-sm">
        <span className="text-red-400 font-medium">No futures data available</span>
        <span className="text-red-300/70 ml-2">
          {curve.message}
          {curve.fallback_etf && (
            <> Consider <span className="font-mono text-red-300">{curve.fallback_etf}</span> ETF as a sector proxy.</>
          )}
        </span>
      </div>
    );
  }

  if (curve.data_quality === "partial") {
    return (
      <div className="bg-yellow-900/20 border border-yellow-800/40 rounded-lg px-4 py-3 text-sm">
        <span className="text-yellow-400 font-medium">Partial data</span>
        <span className="text-yellow-300/70 ml-2">
          {curve.total_contracts} contracts available. Some gaps may exist in the curve.
        </span>
      </div>
    );
  }

  return null;
}
