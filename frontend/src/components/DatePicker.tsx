import { format, subWeeks, subMonths, subYears } from "date-fns";

interface Props {
  value: string | null;
  onChange: (date: string | null) => void;
}

const presets = [
  { label: "1wk ago", fn: () => subWeeks(new Date(), 1) },
  { label: "1mo ago", fn: () => subMonths(new Date(), 1) },
  { label: "3mo ago", fn: () => subMonths(new Date(), 3) },
  { label: "6mo ago", fn: () => subMonths(new Date(), 6) },
  { label: "1yr ago", fn: () => subYears(new Date(), 1) },
  { label: "2yr ago", fn: () => subYears(new Date(), 2) },
];

export default function DatePicker({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <span className="text-sm text-slate-400">Compare to:</span>
      {presets.map((p) => {
        const dateStr = format(p.fn(), "yyyy-MM-dd");
        return (
          <button
            key={p.label}
            onClick={() => onChange(value === dateStr ? null : dateStr)}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
              value === dateStr
                ? "bg-orange-500/20 text-orange-400 ring-1 ring-orange-500/40"
                : "bg-slate-800/50 text-slate-500 hover:text-slate-300 hover:bg-slate-800"
            }`}
          >
            {p.label}
          </button>
        );
      })}
      <input
        type="date"
        value={value || ""}
        onChange={(e) => onChange(e.target.value || null)}
        max={format(new Date(), "yyyy-MM-dd")}
        className="bg-slate-800 text-slate-300 text-xs rounded px-2 py-1 border border-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-500"
      />
      {value && (
        <button
          onClick={() => onChange(null)}
          className="text-xs text-slate-500 hover:text-slate-300"
        >
          Clear
        </button>
      )}
    </div>
  );
}
