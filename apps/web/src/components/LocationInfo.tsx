import { useState } from "react";
import { tileUrl } from "../lib/api";

interface Props {
  lat: number;
  lon: number;
  year: number;
}

export default function LocationInfo({ lat, lon, year }: Props) {
  const [imgError, setImgError] = useState(false);
  const isFuture = year > 2025;

  return (
    <div className="border-b border-chronos-border">
      {/* Satellite thumbnail */}
      <div className="relative h-32 bg-chronos-bg overflow-hidden">
        {!imgError ? (
          <img
            key={`${lat}-${lon}-${year}`}
            src={tileUrl(lat, lon, year)}
            alt={`Satellite view ${year}`}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-700 text-xs">
            No imagery available
          </div>
        )}
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-chronos-panel/80 to-transparent" />
        {/* Year label over image */}
        <div className="absolute bottom-2 left-3 right-3 flex items-end justify-between">
          <div>
            <div className="font-mono text-xs text-slate-400">
              {lat.toFixed(4)}°{lat >= 0 ? "N" : "S"} {lon.toFixed(4)}°{lon >= 0 ? "E" : "W"}
            </div>
          </div>
          <div
            className="text-xs px-2 py-0.5 rounded-full font-semibold"
            style={{
              background: isFuture ? "rgba(168,85,247,0.2)" : "rgba(34,211,238,0.2)",
              color: isFuture ? "#c084fc" : "#22d3ee",
              border: `1px solid ${isFuture ? "#a855f760" : "#22d3ee60"}`,
            }}
          >
            {isFuture ? "~" : ""}{year}
          </div>
        </div>
      </div>
    </div>
  );
}
