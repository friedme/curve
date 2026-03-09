import type { CurvePoint, CurveShape } from "../types";

export function classifyCurveShape(points: CurvePoint[]): CurveShape {
  if (points.length < 2) return "flat";

  const front = points[0].price;
  const back = points[points.length - 1].price;
  const diff = back - front;
  const pct = Math.abs(diff / front) * 100;

  if (pct < 1) return "flat";

  // Check if monotonic
  let rising = 0;
  let falling = 0;
  for (let i = 1; i < points.length; i++) {
    if (points[i].price > points[i - 1].price) rising++;
    else if (points[i].price < points[i - 1].price) falling++;
  }

  const total = rising + falling;
  if (total === 0) return "flat";

  if (rising / total > 0.7) return "contango";
  if (falling / total > 0.7) return "backwardation";
  return "mixed";
}

export function formatPrice(price: number, unit: string): string {
  if (unit.includes("USD")) {
    return `$${price.toFixed(2)}`;
  }
  return `${price.toFixed(2)} ${unit.split("/")[0]}`;
}

export function getShapeColor(shape: CurveShape): string {
  switch (shape) {
    case "contango": return "#22c55e";
    case "backwardation": return "#f97316";
    case "flat": return "#94a3b8";
    case "mixed": return "#a78bfa";
  }
}

export function getShapeDescription(shape: CurveShape): string {
  switch (shape) {
    case "contango": return "Future prices higher than spot (upward sloping)";
    case "backwardation": return "Future prices lower than spot (downward sloping)";
    case "flat": return "Relatively flat curve";
    case "mixed": return "No clear directional pattern";
  }
}
