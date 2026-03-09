export interface CurvePoint {
  tenor: number;
  label: string;
  price: number;
}

export interface ForwardCurve {
  commodity: string;
  slug: string;
  data_quality: "full" | "partial" | "unavailable";
  unit: string;
  as_of: string;
  points: CurvePoint[];
  total_contracts: number;
  fallback_etf?: string;
  message?: string;
}

export interface SpreadPoint {
  tenor: number;
  current_label: string;
  historical_label: string;
  diff: number;
}

export interface CurveComparison {
  current: ForwardCurve;
  historical: ForwardCurve;
  spread: SpreadPoint[];
}

export interface CommodityListItem {
  slug: string;
  display_name: string;
  data_quality: string;
  unit: string;
}

export type CurveShape = "contango" | "backwardation" | "flat" | "mixed";

export interface SpotPrice {
  slug: string;
  display_name: string;
  unit: string;
  price: number;
  contract: string;
}

export interface SpotHistoryPoint {
  date: string;
  price: number;
}

export interface SpotHistory {
  slug: string;
  display_name: string;
  unit: string;
  period: string;
  points: SpotHistoryPoint[];
  history_label?: string | null;
}
