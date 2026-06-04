import type { LoadingStep } from "../App";

const STEPS: { key: LoadingStep; label: string; detail: string }[] = [
  { key: "history", label: "Fetching 40 years of satellite data", detail: "Querying Landsat, VIIRS & MODIS via Earth Engine — first visit takes ~30s" },
  { key: "forecast", label: "Computing scenario forecasts", detail: "Running Prophet model for 2026–2050 across all signals" },
  { key: "narrative", label: "Writing the diary", detail: "Asking Llama 3.3-70B to narrate what happened and what comes next" },
];

export default function LoadingPanel({ step }: { step: LoadingStep }) {
  const currentIdx = STEPS.findIndex((s) => s.key === step);

  return (
    <div className="px-4 py-6 flex flex-col gap-4">
      {STEPS.map((s, i) => {
        const done = i < currentIdx;
        const active = i === currentIdx;
        return (
          <div key={s.key} className="flex gap-3 items-start">
            {/* Step indicator */}
            <div className="shrink-0 mt-0.5">
              {done ? (
                <div className="w-5 h-5 rounded-full bg-emerald-500/20 border border-emerald-500 flex items-center justify-center text-emerald-400 text-xs">✓</div>
              ) : active ? (
                <div className="w-5 h-5 rounded-full border border-chronos-accent flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-chronos-accent animate-ping" />
                </div>
              ) : (
                <div className="w-5 h-5 rounded-full border border-chronos-border" />
              )}
            </div>
            {/* Text */}
            <div>
              <div className={`text-sm font-medium ${active ? "text-white" : done ? "text-emerald-400" : "text-slate-600"}`}>
                {s.label}
              </div>
              {active && (
                <div className="text-xs text-slate-500 mt-0.5">{s.detail}</div>
              )}
            </div>
          </div>
        );
      })}

      {/* Animated bar */}
      <div className="mt-2 h-0.5 bg-chronos-border rounded-full overflow-hidden">
        <div
          className="h-full bg-chronos-accent rounded-full transition-all duration-700"
          style={{ width: `${((currentIdx + 1) / STEPS.length) * 100}%` }}
        />
      </div>
      <p className="text-xs text-slate-600 text-center -mt-2">
        Cached coordinates load instantly on repeat visits
      </p>
    </div>
  );
}
