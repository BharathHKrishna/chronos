import { useState, useCallback } from "react";
import MapView from "./components/Map";
import Timeline from "./components/Timeline";
import SignalCharts from "./components/SignalCharts";
import Diary from "./components/Diary";
import ScenarioSelector from "./components/ScenarioSelector";
import LocationInfo from "./components/LocationInfo";
import { fetchHistory, fetchForecast, fetchNarrative, DEMO_LOCATIONS } from "./lib/api";
import type { HistoryData, ForecastData } from "./lib/api";

export type Scenario = "bau" | "solar" | "grid" | "stress";

const TODAY = 2025;
const MIN_YEAR = 1985;
const MAX_YEAR = 2050;

export default function App() {
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [year, setYear] = useState<number>(TODAY);
  const [scenario, setScenario] = useState<Scenario>("bau");
  const [history, setHistory] = useState<HistoryData | null>(null);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [narrative, setNarrative] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const loadLocation = useCallback(
    async (lat: number, lon: number, sc: Scenario = scenario) => {
      setLoading(true);
      setError("");
      setCoords({ lat, lon });
      try {
        const hist = await fetchHistory(lat, lon);
        setHistory(hist);
        const fore = await fetchForecast(lat, lon, sc);
        setForecast(fore);
        const narr = await fetchNarrative(lat, lon, sc, hist, fore);
        setNarrative(narr);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    [scenario]
  );

  const handleScenarioChange = async (sc: Scenario) => {
    setScenario(sc);
    if (coords) {
      await loadLocation(coords.lat, coords.lon, sc);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-chronos-bg overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-chronos-border z-10">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Chronos</h1>
          <p className="text-xs text-slate-400">The past &amp; future of any place on Earth</p>
        </div>
        <div className="flex gap-2">
          {DEMO_LOCATIONS.slice(0, 5).map((loc) => (
            <button
              key={loc.name}
              onClick={() => loadLocation(loc.lat, loc.lon)}
              className="text-xs px-2 py-1 rounded bg-chronos-panel border border-chronos-border text-slate-300 hover:text-white hover:border-chronos-accent transition-colors"
            >
              {loc.name}
            </button>
          ))}
        </div>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map */}
        <div className="flex-1 relative">
          <MapView
            onLocationClick={loadLocation}
            selectedCoords={coords}
            year={year}
          />
          {loading && (
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
              <div className="text-white text-sm animate-pulse">Loading satellite data…</div>
            </div>
          )}
        </div>

        {/* Right panel */}
        {coords && (
          <aside className="w-96 flex flex-col bg-chronos-panel border-l border-chronos-border overflow-y-auto">
            <LocationInfo lat={coords.lat} lon={coords.lon} year={year} />

            <div className="px-4 py-3 border-b border-chronos-border">
              <ScenarioSelector value={scenario} onChange={handleScenarioChange} />
            </div>

            {error && (
              <div className="mx-4 mt-3 p-3 rounded bg-red-900/30 border border-red-700 text-red-300 text-xs">
                {error}
              </div>
            )}

            {history && (
              <SignalCharts
                history={history}
                forecast={forecast}
                currentYear={year}
              />
            )}

            {narrative && <Diary text={narrative} scenario={scenario} year={year} />}
          </aside>
        )}
      </div>

      {/* Timeline */}
      <footer className="border-t border-chronos-border bg-chronos-panel px-6 py-4">
        <Timeline
          year={year}
          onChange={setYear}
          min={MIN_YEAR}
          max={MAX_YEAR}
          today={TODAY}
          disabled={!coords}
        />
      </footer>
    </div>
  );
}
