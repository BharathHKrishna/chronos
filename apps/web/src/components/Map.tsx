import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMapEvents, useMap } from "react-leaflet";
import type { LatLng } from "leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface Props {
  onLocationClick: (lat: number, lon: number) => void;
  selectedCoords: { lat: number; lon: number } | null;
  year: number;
  loading: boolean;
}

function ClickHandler({
  onLocationClick,
  loading,
}: {
  onLocationClick: (lat: number, lon: number) => void;
  loading: boolean;
}) {
  useMapEvents({
    click(e: { latlng: LatLng }) {
      if (!loading) onLocationClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function MarkerLayer({ coords }: { coords: { lat: number; lon: number } | null }) {
  const map = useMap();
  const markerRef = useRef<L.Marker | null>(null);

  useEffect(() => {
    if (!coords) return;
    markerRef.current?.remove();
    const icon = L.divIcon({
      className: "",
      html: `
        <div style="position:relative;width:20px;height:20px">
          <div style="position:absolute;inset:0;border-radius:50%;background:rgba(79,142,247,0.25);animation:ping 1.5s ease-out infinite"></div>
          <div style="position:absolute;top:3px;left:3px;width:14px;height:14px;border-radius:50%;background:#4f8ef7;border:2px solid white;box-shadow:0 0 8px rgba(79,142,247,0.8)"></div>
        </div>
        <style>@keyframes ping{0%{transform:scale(1);opacity:.8}100%{transform:scale(2.5);opacity:0}}</style>
      `,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    });
    markerRef.current = L.marker([coords.lat, coords.lon], { icon }).addTo(map);
    map.flyTo([coords.lat, coords.lon], Math.max(map.getZoom(), 8), { duration: 1.0 });
    return () => { markerRef.current?.remove(); };
  }, [coords, map]);

  return null;
}

export default function MapView({ onLocationClick, selectedCoords, year, loading }: Props) {
  const isFuture = year > 2025;

  return (
    <div className="relative w-full h-full" style={{ cursor: loading ? "wait" : "crosshair" }}>
      <MapContainer
        center={[20, 0]}
        zoom={3}
        style={{ height: "100%", width: "100%", background: "#0f1117" }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com">CARTO</a>'
          maxZoom={19}
        />
        <ClickHandler onLocationClick={onLocationClick} loading={loading} />
        <MarkerLayer coords={selectedCoords} />
      </MapContainer>

      {/* Year badge */}
      <div
        className="absolute top-3 left-3 z-[1000] px-3 py-1.5 rounded-full text-sm font-bold backdrop-blur-sm"
        style={{
          background: isFuture ? "rgba(168,85,247,0.15)" : "rgba(34,211,238,0.15)",
          border: `1px solid ${isFuture ? "#a855f7" : "#22d3ee"}`,
          color: isFuture ? "#c084fc" : "#22d3ee",
        }}
      >
        {isFuture ? "~" : ""}{year}
        {isFuture && <span className="ml-1.5 text-xs opacity-60 font-normal">projected</span>}
      </div>

      {/* Zoom controls */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-1">
        <ZoomBtn dir="in" />
        <ZoomBtn dir="out" />
      </div>

      {/* First-click prompt */}
      {!selectedCoords && !loading && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-[500]">
          <div className="text-center">
            <div className="text-5xl mb-3 opacity-40">🌍</div>
            <div className="text-slate-400 text-sm font-medium">Click any point on the map</div>
            <div className="text-slate-600 text-xs mt-1">or choose a demo location above</div>
          </div>
        </div>
      )}
    </div>
  );
}

function ZoomBtn({ dir }: { dir: "in" | "out" }) {
  return (
    <button
      onClick={() => {
        const map = (window as unknown as { _leaflet_map?: L.Map })._leaflet_map;
        if (map) dir === "in" ? map.zoomIn() : map.zoomOut();
      }}
      className="w-8 h-8 flex items-center justify-center rounded bg-chronos-panel/80 border border-chronos-border text-slate-300 hover:text-white hover:bg-chronos-panel backdrop-blur-sm text-lg leading-none"
    >
      {dir === "in" ? "+" : "−"}
    </button>
  );
}
