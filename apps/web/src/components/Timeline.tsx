interface Props {
  year: number;
  onChange: (year: number) => void;
  min: number;
  max: number;
  today: number;
  disabled: boolean;
}

const TODAY_COLOR = "#4f8ef7";
const PAST_COLOR = "#22d3ee";
const FUTURE_COLOR = "#a855f7";

export default function Timeline({ year, onChange, min, max, today, disabled }: Props) {
  const isFuture = year > today;
  const pctToday = ((today - min) / (max - min)) * 100;
  const pctCurrent = ((year - min) / (max - min)) * 100;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>{min}</span>
        <span className="text-slate-300 font-semibold">
          {isFuture ? `~${year} (projected)` : year}
        </span>
        <span>{max}</span>
      </div>

      <div className="relative flex items-center h-8">
        {/* Track */}
        <div className="absolute inset-0 flex items-center">
          <div className="w-full h-1.5 rounded-full bg-chronos-border relative">
            {/* Past fill */}
            <div
              className="absolute top-0 left-0 h-full rounded-l-full transition-all"
              style={{
                width: `${Math.min(pctCurrent, pctToday)}%`,
                background: PAST_COLOR,
                opacity: 0.6,
              }}
            />
            {/* Future fill */}
            {isFuture && (
              <div
                className="absolute top-0 h-full transition-all"
                style={{
                  left: `${pctToday}%`,
                  width: `${pctCurrent - pctToday}%`,
                  background: FUTURE_COLOR,
                  opacity: 0.6,
                }}
              />
            )}
            {/* Today marker */}
            <div
              className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 border-white z-10"
              style={{ left: `${pctToday}%`, transform: "translate(-50%, -50%)", background: TODAY_COLOR }}
            />
          </div>
        </div>

        {/* Range input */}
        <input
          type="range"
          min={min}
          max={max}
          value={year}
          disabled={disabled}
          onChange={(e) => onChange(Number(e.target.value))}
          className="relative w-full h-8 appearance-none bg-transparent cursor-pointer disabled:cursor-not-allowed z-20"
          style={{
            accentColor: isFuture ? FUTURE_COLOR : PAST_COLOR,
          }}
        />
      </div>

      <div className="flex justify-between text-xs text-slate-500">
        <span>← Historical data</span>
        <span className="text-slate-400">TODAY</span>
        <span>Projected future →</span>
      </div>
    </div>
  );
}
