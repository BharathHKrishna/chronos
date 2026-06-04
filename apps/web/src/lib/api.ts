const BASE = import.meta.env.VITE_API_BASE_URL ?? "https://chronos-api-8ok9.onrender.com";

export interface SignalPoint {
  year: number;
  value: number | null;
  source?: string;
  lower?: number;
  upper?: number;
}

export interface HistoryData {
  ndvi: SignalPoint[];
  nighttime_lights: SignalPoint[];
  land_surface_temp: SignalPoint[];
  built_up_extent: SignalPoint[];
}

export interface ForecastData {
  scenario: string;
  signals: HistoryData;
}

export async function fetchHistory(lat: number, lon: number): Promise<HistoryData> {
  const r = await fetch(`${BASE}/history?lat=${lat}&lon=${lon}`);
  if (!r.ok) throw new Error(`History fetch failed: ${r.status}`);
  const json = await r.json();
  return json.data as HistoryData;
}

export async function fetchForecast(
  lat: number,
  lon: number,
  scenario: string
): Promise<ForecastData> {
  const r = await fetch(`${BASE}/forecast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lon, scenario }),
  });
  if (!r.ok) throw new Error(`Forecast fetch failed: ${r.status}`);
  const json = await r.json();
  return json.data as ForecastData;
}

export async function fetchNarrative(
  lat: number,
  lon: number,
  scenario: string,
  history: HistoryData,
  forecast: ForecastData
): Promise<string> {
  const r = await fetch(`${BASE}/narrative`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lon, scenario, history, forecast }),
  });
  if (!r.ok) throw new Error(`Narrative fetch failed: ${r.status}`);
  const json = await r.json();
  return json.narrative as string;
}

export function tileUrl(lat: number, lon: number, year: number): string {
  return `${BASE}/tile/${year}?lat=${lat}&lon=${lon}`;
}

export const DEMO_LOCATIONS = [
  { name: "Bangalore", lat: 12.97, lon: 77.59 },
  { name: "Sahara Solar Belt", lat: 23.0, lon: 5.0 },
  { name: "Amazon Frontier", lat: -8.5, lon: -55.0 },
  { name: "Karlsruhe", lat: 49.0, lon: 8.4 },
  { name: "Yangtze Delta", lat: 31.2, lon: 121.5 },
  { name: "Aral Sea", lat: 45.0, lon: 60.0 },
  { name: "Dubai", lat: 25.2, lon: 55.3 },
  { name: "Inner Mongolia", lat: 41.0, lon: 111.0 },
  { name: "Lagos", lat: 6.5, lon: 3.4 },
  { name: "Houston", lat: 29.7, lon: -95.0 },
];
