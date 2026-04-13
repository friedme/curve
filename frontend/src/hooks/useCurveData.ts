import { useQuery } from "@tanstack/react-query";
import { fetchCommodities, fetchCurve, fetchCurveComparison, fetchCurveEvolution, fetchSpotPrices, fetchSpotHistory, fetchSpreadHistory } from "../api/curveApi";

export function useCommodities() {
  return useQuery({
    queryKey: ["commodities"],
    queryFn: fetchCommodities,
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}

export function useCurrentCurve(slug: string) {
  return useQuery({
    queryKey: ["curve", slug],
    queryFn: () => fetchCurve(slug),
    staleTime: 2 * 60 * 1000,
    enabled: !!slug,
  });
}

export function useCurveComparison(slug: string, historicalDate: string | null) {
  return useQuery({
    queryKey: ["curve-compare", slug, historicalDate],
    queryFn: () => fetchCurveComparison(slug, historicalDate!),
    staleTime: 5 * 60 * 1000,
    enabled: !!slug && !!historicalDate,
  });
}

export function useCurveEvolution(slug: string) {
  return useQuery({
    queryKey: ["curve-evolution", slug],
    queryFn: () => fetchCurveEvolution(slug),
    staleTime: 5 * 60 * 1000,
    enabled: !!slug,
  });
}

export function useSpreadHistory(slug: string) {
  return useQuery({
    queryKey: ["spread-history", slug],
    queryFn: () => fetchSpreadHistory(slug),
    staleTime: 5 * 60 * 1000,
    enabled: !!slug,
  });
}

export function useSpotPrices() {
  return useQuery({
    queryKey: ["spot-prices"],
    queryFn: fetchSpotPrices,
    staleTime: 5 * 60 * 1000,
  });
}

export function useSpotHistory(slug: string | null, period: string = "1y") {
  return useQuery({
    queryKey: ["spot-history", slug, period],
    queryFn: () => fetchSpotHistory(slug!, period),
    staleTime: 60 * 60 * 1000, // 1hr
    enabled: !!slug,
  });
}
