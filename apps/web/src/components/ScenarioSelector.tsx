import type { Scenario } from "../App";

const SCENARIOS: { id: Scenario; label: string; desc: string; color: string }[] = [
  { id: "bau", label: "Business as usual", desc: "Extrapolate historical trends", color: "#94a3b8" },
  { id: "solar", label: "Solar buildout", desc: "Aggressive renewable transition", color: "#fbbf24" },
  { id: "grid", label: "Grid expansion", desc: "Electrification accelerates", color: "#4f8ef7" },
  { id: "stress", label: "Climate stress", desc: "Accelerated warming & land pressure", color: "#f87171" },
];

interface Props {
  value: Scenario;
  onChange: (s: Scenario) => void;
  disabled?: boolean;
}

export default function ScenarioSelector({ value, onChange, disabled }: Props) {
  return (
    <div>
      <div className="text-xs text-slate-400 uppercase tracking-wider mb-2 font-semibold">
        Future scenario (2026–2050)
      </div>
      <div className="grid grid-cols-2 gap-1.5">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            onClick={() => !disabled && onChange(s.id)}
            disabled={disabled}
            className="text-left px-2.5 py-2 rounded border transition-all text-xs disabled:opacity-40 disabled:cursor-not-allowed"
            style={{
              borderColor: value === s.id ? s.color : "#2a2d3e",
              background: value === s.id ? s.color + "18" : "transparent",
              color: value === s.id ? s.color : "#94a3b8",
            }}
          >
            <div className="font-semibold">{s.label}</div>
            <div className="opacity-70 mt-0.5">{s.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
