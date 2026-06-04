interface Props {
  lat: number;
  lon: number;
  year: number;
}

export default function LocationInfo({ lat, lon, year }: Props) {
  return (
    <div className="px-4 py-3 border-b border-chronos-border">
      <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-1">Location</div>
      <div className="font-mono text-sm text-slate-200">
        {lat.toFixed(4)}° {lat >= 0 ? "N" : "S"}, {lon.toFixed(4)}° {lon >= 0 ? "E" : "W"}
      </div>
      <div className="text-xs text-slate-500 mt-1">
        Viewing {year > 2025 ? `~${year} (projected)` : year}
      </div>
    </div>
  );
}
