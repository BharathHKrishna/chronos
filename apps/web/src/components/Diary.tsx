import type { Scenario } from "../App";

const SCENARIO_LABELS: Record<Scenario, string> = {
  bau: "Business as usual",
  solar: "Solar buildout",
  grid: "Grid expansion",
  stress: "Climate stress",
};

const SCENARIO_COLORS: Record<Scenario, string> = {
  bau: "#94a3b8",
  solar: "#fbbf24",
  grid: "#4f8ef7",
  stress: "#f87171",
};

interface Props {
  text: string;
  scenario: Scenario;
  year: number;
}

export default function Diary({ text, scenario, year }: Props) {
  const isFuture = year > 2025;
  return (
    <div className="px-4 py-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {isFuture ? "Projected diary" : "Historical diary"}
        </div>
        {isFuture && (
          <span
            className="text-xs px-2 py-0.5 rounded-full border"
            style={{ color: SCENARIO_COLORS[scenario], borderColor: SCENARIO_COLORS[scenario] + "44" }}
          >
            {SCENARIO_LABELS[scenario]}
          </span>
        )}
      </div>
      <p className="text-sm text-slate-300 leading-relaxed italic">
        {text}
      </p>
      {isFuture && (
        <p className="mt-2 text-xs text-slate-500">
          Projections are indicative and scenario-dependent. Confidence bands reflect model uncertainty.
        </p>
      )}
    </div>
  );
}
