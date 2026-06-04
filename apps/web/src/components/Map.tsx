import { useEffect, useRef } from "react";
import { MapContainer, TileLayer, useMapEvents, useMap } from "react-leaflet";
import type { LatLng } from "leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface Props {
  onLocationClick: (lat: number, lon: number) => void;
  selectedCoords: { lat: number; lon: number } | null;
  year: number;
}

function ClickHandler({ onLocationClick }: { onLocationClick: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(e: { latlng: LatLng }) {
      onLocationClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function MarkerLayer({ coords }: { coords: { lat: number; lon: number } | null }) {
  const map = useMap();
  const markerRef = useRef<L.Marker | null>(null);

  useEffect(() => {
    if (!coords) return;
    if (markerRef.current) markerRef.current.remove();
    const icon = L.divIcon({
      className: "",
      html: `<div style="width:14px;height:14px;border-radius:50%;background:#4f8ef7;border:2px solid white;box-shadow:0 0 8px rgba(79,142,247,0.8)"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });
    markerRef.current = L.marker([coords.lat, coords.lon], { icon }).addTo(map);
    map.flyTo([coords.lat, coords.lon], Math.max(map.getZoom(), 9), { duration: 0.8 });
    return () => {
      markerRef.current?.remove();
    };
  }, [coords, map]);

  return null;
}

export default function MapView({ onLocationClick, selectedCoords, year }: Props) {
  const isFuture = year > 2025;

  return (
    <div className="relative w-full h-full">
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
        {/* Satellite overlay for selected location */}
        {selectedCoords && (
          <TileLayer
            key={`${selectedCoords.lat}-${selectedCoords.lon}-${year}`}
            url={`/tile/${year}?lat=${selectedCoords.lat}&lon=${selectedCoords.lon}`}
            opacity={0.7}
          />
        )}
        <ClickHandler onLocationClick={onLocationClick} />
        <MarkerLayer coords={selectedCoords} />
      </MapContainer>

      {/* Year badge */}
      <div
        className="absolute top-3 left-3 z-[1000] px-3 py-1 rounded-full text-sm font-bold"
        style={{
          background: isFuture ? "rgba(168,85,247,0.2)" : "rgba(34,211,238,0.2)",
          border: `1px solid ${isFuture ? "#a855f7" : "#22d3ee"}`,
          color: isFuture ? "#c084fc" : "#22d3ee",
        }}
      >
        {isFuture ? "~" : ""}{year}
        {isFuture && <span className="ml-1 text-xs opacity-70">projected</span>}
      </div>

      {!selectedCoords && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-[500]">
          <div className="text-center text-slate-500">
            <div className="text-4xl mb-2">🌍</div>
            <div className="text-sm">Click any point on the map</div>
          </div>
        </div>
      )}
    </div>
  );
}
