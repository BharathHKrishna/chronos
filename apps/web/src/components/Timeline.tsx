interface Props {
  year: number;
  onChange: (year: number) => void;
  min: number;
  max: number;
  today: number;
  disabled: boolean;
}

const TICK_YEARS = [1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030, 2035, 2040, 2045, 2050];

export default function Timeline({ year, onChange, min, max, today, disabled }: Props) {
  const isFuture = year > today;
  const pct = (v: number) => ((v - min) / (max - min)) * 100;

  return (
    <div className="flex flex-col gap-1 select-none">
      {/* Year display */}
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-500">{min}</span>
        <span className={`text-base font-bold tabular-nums ${isFuture ? "text-purple-400" : "text-cyan-400"}`}>
          {isFuture ? "~" : ""}{year}
          {isFuture && <span className="ml-1.5 text-xs font-normal text-slate-500">projected</span>}
        </span>
        <span className="text-xs text-slate-500">{max}</span>
      </div>

      {/* Slider track */}
      <div className="relative h-8 flex items-center">
        {/* Background track */}
        <div className="absolute w-full h-1.5 rounded-full bg-chronos-border" />

        {/* Past fill */}
        <div
          className="absolute h-1.5 rounded-l-full transition-all duration-75"
          style={{ width: `${Math.min(pct(year), pct(today))}%`, background: "#22d3ee", opacity: 0.5 }}
        />

        {/* Future fill */}
        {isFuture && (
          <div
            className="absolute h-1.5 transition-all duration-75"
            style={{ left: `${pct(today)}%`, width: `${pct(year) - pct(today)}%`, background: "#a855f7", opacity: 0.5 }}
          />
        )}

        {/* Today marker */}
        <div
          className="absolute w-0.5 h-4 rounded-full bg-chronos-accent z-10"
          style={{ left: `${pct(today)}%`, transform: "translateX(-50%)" }}
        />

        {/* Range input */}
        <input
          type="range"
          min={min}
          max={max}
          value={year}
          disabled={disabled}
          onChange={(e) => onChange(Number(e.target.value))}
          className="absolute w-full h-8 appearance-none bg-transparent cursor-pointer disabled:cursor-not-allowed z-20"
          style={{ accentColor: isFuture ? "#a855f7" : "#22d3ee" }}
        />
      </div>

      {/* Tick labels */}
      <div className="relative h-4">
        {TICK_YEARS.map((y) => (
          <button
            key={y}
            onClick={() => !disabled && onChange(y)}
            disabled={disabled}
            className="absolute -translate-x-1/2 text-xs text-slate-600 hover:text-slate-400 transition-colors disabled:cursor-not-allowed tabular-nums"
            style={{ left: `${pct(y)}%` }}
          >
            {y === today ? <span className="text-chronos-accent font-semibold">{y}</span> : y}
          </button>
        ))}
      </div>

      {/* Labels */}
      <div className="flex justify-between text-xs text-slate-600 mt-1">
        <span>← Historical satellite data</span>
        <span>AI-projected future →</span>
      </div>
    </div>
  );
}
