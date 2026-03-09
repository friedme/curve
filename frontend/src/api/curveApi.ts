import type { CommodityListItem, CurveComparison, ForwardCurve, SpotHistory, SpotPrice } from "../types";

const BASE = "/api";

export async function fetchCommodities(): Promise<CommodityListItem[]> {
  const res = await fetch(`${BASE}/commodities`);
  if (!res.ok) throw new Error("Failed to fetch commodities");
  return res.json();
}

export async function fetchCurve(slug: string): Promise<ForwardCurve> {
  const res = await fetch(`${BASE}/curve/${slug}`);
  if (!res.ok) throw new Error(`Failed to fetch curve for ${slug}`);
  return res.json();
}

export async function fetchCurveComparison(
  slug: string,
  historicalDate: string
): Promise<CurveComparison> {
  const res = await fetch(
    `${BASE}/curve/${slug}/compare?historical_date=${historicalDate}`
  );
  if (!res.ok) throw new Error(`Failed to fetch comparison for ${slug}`);
  return res.json();
}

export async function fetchSpotPrices(): Promise<SpotPrice[]> {
  const res = await fetch(`${BASE}/spot-prices`);
  if (!res.ok) throw new Error("Failed to fetch spot prices");
  return res.json();
}

export async function fetchSpotHistory(slug: string, period: string = "1y"): Promise<SpotHistory> {
  const res = await fetch(`${BASE}/spot-history/${slug}?period=${period}`);
  if (!res.ok) throw new Error(`Failed to fetch spot history for ${slug}`);
  return res.json();
}
