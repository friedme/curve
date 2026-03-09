import { useCommodities } from "../hooks/useCurveData";

const qualityDot: Record<string, string> = {
  full: "bg-green-400",
  partial: "bg-yellow-400",
  front_only: "bg-orange-400",
  unavailable: "bg-red-400",
};

interface Props {
  selected: string;
  onChange: (slug: string) => void;
}

export default function CommoditySelector({ selected, onChange }: Props) {
  const { data: commodities, isLoading } = useCommodities();

  if (isLoading) {
    return <div className="text-slate-500 text-sm">Loading commodities...</div>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {commodities?.map((c) => (
        <button
          key={c.slug}
          onClick={() => onChange(c.slug)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            selected === c.slug
              ? "bg-slate-700 text-white ring-1 ring-slate-500"
              : "bg-slate-800/50 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          } ${c.data_quality === "unavailable" ? "opacity-50" : ""}`}
        >
          <span className={`w-2 h-2 rounded-full ${qualityDot[c.data_quality] || "bg-gray-500"}`} />
          {c.display_name}
        </button>
      ))}
    </div>
  );
}
