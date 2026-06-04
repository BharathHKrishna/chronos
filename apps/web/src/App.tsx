import { useState, useCallback, useEffect } from "react";
import MapView from "./components/Map";
import Timeline from "./components/Timeline";
import SignalCharts from "./components/SignalCharts";
import Diary from "./components/Diary";
import ScenarioSelector from "./components/ScenarioSelector";
import LocationInfo from "./components/LocationInfo";
import LoadingPanel from "./components/LoadingPanel";
import { fetchHistory, fetchForecast, fetchNarrative, DEMO_LOCATIONS } from "./lib/api";
import type { HistoryData, ForecastData } from "./lib/api";

export type Scenario = "bau" | "solar" | "grid" | "stress";
export type LoadingStep = "history" | "forecast" | "narrative" | null;

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
  const [loadingStep, setLoadingStep] = useState<LoadingStep>(null);
  const [error, setError] = useState<string>("");

  // Keyboard scrubbing: ← → arrow keys
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!coords) return;
      if (e.key === "ArrowLeft") setYear((y) => Math.max(MIN_YEAR, y - 1));
      if (e.key === "ArrowRight") setYear((y) => Math.min(MAX_YEAR, y + 1));
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [coords]);

  const loadLocation = useCallback(
    async (lat: number, lon: number, sc: Scenario = scenario) => {
      setLoadingStep("history");
      setError("");
      setHistory(null);
      setForecast(null);
      setNarrative("");
      setCoords({ lat, lon });
      try {
        const hist = await fetchHistory(lat, lon);
        setHistory(hist);

        setLoadingStep("forecast");
        const fore = await fetchForecast(lat, lon, sc);
        setForecast(fore);

        setLoadingStep("narrative");
        const narr = await fetchNarrative(lat, lon, sc, hist, fore);
        setNarrative(narr);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoadingStep(null);
      }
    },
    [scenario]
  );

  const handleScenarioChange = async (sc: Scenario) => {
    setScenario(sc);
    if (coords) await loadLocation(coords.lat, coords.lon, sc);
  };

  return (
    <div className="flex flex-col h-screen bg-chronos-bg overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-chronos-border z-10 shrink-0">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">Chronos</h1>
          <p className="text-xs text-slate-400">The past &amp; future of any place on Earth</p>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {DEMO_LOCATIONS.slice(0, 5).map((loc) => (
            <button
              key={loc.name}
              onClick={() => loadLocation(loc.lat, loc.lon)}
              disabled={loadingStep !== null}
              className="text-xs px-2 py-1 rounded bg-chronos-panel border border-chronos-border text-slate-300 hover:text-white hover:border-chronos-accent transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
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
            loading={loadingStep !== null}
          />
        </div>

        {/* Right panel — always visible once coords selected */}
        {coords && (
          <aside className="w-96 flex flex-col bg-chronos-panel border-l border-chronos-border overflow-y-auto shrink-0">
            <LocationInfo lat={coords.lat} lon={coords.lon} year={year} />

            <div className="px-4 py-3 border-b border-chronos-border">
              <ScenarioSelector
                value={scenario}
                onChange={handleScenarioChange}
                disabled={loadingStep !== null}
              />
            </div>

            {error && (
              <div className="mx-4 mt-3 p-3 rounded bg-red-900/30 border border-red-700 text-red-300 text-xs flex items-start gap-2">
                <span>⚠</span>
                <div>
                  <div className="font-semibold mb-0.5">Failed to load data</div>
                  <div>{error}</div>
                  <button
                    onClick={() => loadLocation(coords.lat, coords.lon)}
                    className="mt-2 text-red-400 underline hover:text-red-300"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}

            {loadingStep !== null && <LoadingPanel step={loadingStep} />}

            {history && !loadingStep && (
              <SignalCharts history={history} forecast={forecast} currentYear={year} />
            )}

            {narrative && !loadingStep && (
              <Diary text={narrative} scenario={scenario} year={year} />
            )}
          </aside>
        )}
      </div>

      {/* Timeline */}
      <footer className="border-t border-chronos-border bg-chronos-panel px-6 py-4 shrink-0">
        <Timeline
          year={year}
          onChange={setYear}
          min={MIN_YEAR}
          max={MAX_YEAR}
          today={TODAY}
          disabled={!coords}
        />
        {coords && (
          <div className="text-center text-xs text-slate-600 mt-1">
            ← → arrow keys to scrub
          </div>
        )}
      </footer>
    </div>
  );
}
