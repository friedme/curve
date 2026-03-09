import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CommoditySelector from "./components/CommoditySelector";
import DatePicker from "./components/DatePicker";
import ForwardCurveChart from "./components/ForwardCurveChart";
import SpreadChart from "./components/SpreadChart";
import CurveMetrics from "./components/CurveMetrics";
import DataQualityBanner from "./components/DataQualityBanner";
import SpotPrices from "./components/SpotPrices";
import { useCurrentCurve, useCurveComparison, useSpotPrices } from "./hooks/useCurveData";

const queryClient = new QueryClient();

function Dashboard() {
  const [selectedCommodity, setSelectedCommodity] = useState("brent");
  const [historicalDate, setHistoricalDate] = useState<string | null>(null);

  const { data: currentCurve, isLoading: loadingCurrent, error: errorCurrent } =
    useCurrentCurve(selectedCommodity);
  const { data: comparison, isLoading: loadingComparison } =
    useCurveComparison(selectedCommodity, historicalDate);
  const { data: spotPrices } = useSpotPrices();

  const isLoading = loadingCurrent || (historicalDate && loadingComparison);

  return (
    <div className="min-h-screen bg-[#0a0e17]">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-slate-100 mb-1">
            Commodity Forward Curves
          </h1>
          <p className="text-sm text-slate-500">
            Live futures curve data with historical comparison
          </p>
        </div>

        {/* Controls */}
        <div className="space-y-3 mb-6">
          <CommoditySelector
            selected={selectedCommodity}
            onChange={setSelectedCommodity}
          />
          <DatePicker value={historicalDate} onChange={setHistoricalDate} />
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center gap-2 text-slate-500 text-sm py-8">
            <div className="w-4 h-4 border-2 border-slate-600 border-t-slate-300 rounded-full animate-spin" />
            Fetching curve data...
          </div>
        )}

        {/* Error */}
        {errorCurrent && (
          <div className="bg-red-900/20 border border-red-800/40 rounded-lg px-4 py-3 text-sm text-red-400">
            Failed to load curve data. The backend may not be running.
          </div>
        )}

        {/* Content */}
        {currentCurve && !isLoading && (
          <div className="space-y-4">
            <DataQualityBanner curve={currentCurve} />

            <CurveMetrics
              current={currentCurve}
              historical={comparison?.historical}
            />

            <ForwardCurveChart
              current={currentCurve}
              historical={comparison?.historical}
            />

            {comparison && (
              <SpreadChart
                spread={comparison.spread}
                unit={currentCurve.unit}
              />
            )}

            {spotPrices && <SpotPrices prices={spotPrices} />}
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}
