"use client";

import {
  MapContainer as LeafletMap,
  TileLayer,
  Polyline,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";
import { useEffect, useMemo } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const CITY_CENTER: [number, number] = [13.053, 80.213];
const DEFAULT_ZOOM = 13;

const FACILITY_COLORS: Record<string, string> = {
  hospital: "#EF4444",
  school: "#4ADE80",
  fire_station: "#F59E0B",
  police_station: "#00D4FF",
  bus_stop: "#94A3B8",
  parking: "#A78BFA",
};

type Coordinate = [number, number];

interface Road {
  id: number;
  name: string;
  road_class?: string;
  speed_kmph?: number;
  capacity_vph?: number;
  node_a_lat: number;
  node_a_lon: number;
  node_b_lat: number;
  node_b_lon: number;
  geometry?: Coordinate[];
}

interface Facility {
  id: number;
  name: string;
  facility_type: string;
  lat: number;
  lon: number;
}

interface Props {
  roads: Road[];
  facilities: Facility[];
  onRoadSelect: (road: Road) => void;
  selectedRoad: Road | null;
}

function isValidCoordinate(lat: unknown, lon: unknown): boolean {
  return (
    typeof lat === "number" &&
    typeof lon === "number" &&
    Number.isFinite(lat) &&
    Number.isFinite(lon) &&
    lat >= -90 &&
    lat <= 90 &&
    lon >= -180 &&
    lon <= 180
  );
}

/**
 * Use detailed road geometry when available.
 * Otherwise, fall back to valid road endpoints.
 */
function getRoadPositions(road: Road): Coordinate[] {
  if (Array.isArray(road.geometry)) {
    const geometry = road.geometry.filter(
      (point): point is Coordinate =>
        Array.isArray(point) &&
        point.length >= 2 &&
        isValidCoordinate(point[0], point[1])
    );

    if (geometry.length >= 2) {
      return geometry;
    }
  }

  if (
    isValidCoordinate(road.node_a_lat, road.node_a_lon) &&
    isValidCoordinate(road.node_b_lat, road.node_b_lon)
  ) {
    return [
      [road.node_a_lat, road.node_a_lon],
      [road.node_b_lat, road.node_b_lon],
    ];
  }

  return [];
}

function MapController({
  roads,
  facilities,
}: {
  roads: Road[];
  facilities: Facility[];
}) {
  const map = useMap();

  const points = useMemo(() => {
    const coordinates: Coordinate[] = [];

    roads.forEach((road) => {
      coordinates.push(...getRoadPositions(road));
    });

    facilities.forEach((facility) => {
      if (isValidCoordinate(facility.lat, facility.lon)) {
        coordinates.push([facility.lat, facility.lon]);
      }
    });

    return coordinates;
  }, [roads, facilities]);

  useEffect(() => {
    if (points.length === 0) {
      map.setView(CITY_CENTER, DEFAULT_ZOOM);
      return;
    }

    if (points.length === 1) {
      map.setView(points[0], DEFAULT_ZOOM);
      return;
    }

    map.fitBounds(L.latLngBounds(points), {
      padding: [35, 35],
      maxZoom: 15,
    });
  }, [map, points]);

  return null;
}

function MapControls() {
  const map = useMap();

  const fitAll = () => {
    const bounds = L.latLngBounds([]);

    map.eachLayer((layer) => {
      if (layer instanceof L.Polyline) {
        bounds.extend(layer.getBounds());
      } else if (layer instanceof L.CircleMarker) {
        bounds.extend(layer.getLatLng());
      }
    });

    if (bounds.isValid()) {
      map.fitBounds(bounds, {
        padding: [35, 35],
        maxZoom: 15,
      });
    } else {
      map.setView(CITY_CENTER, DEFAULT_ZOOM);
    }
  };

  return (
    <div className="absolute right-4 top-4 z-[1000] flex flex-col gap-2">
      <button
        type="button"
        aria-label="Zoom in"
        title="Zoom in"
        onClick={() => map.zoomIn()}
        className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-[#0d1826] text-xl text-white shadow-lg hover:bg-slate-800"
      >
        +
      </button>

      <button
        type="button"
        aria-label="Zoom out"
        title="Zoom out"
        onClick={() => map.zoomOut()}
        className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-[#0d1826] text-xl text-white shadow-lg hover:bg-slate-800"
      >
        −
      </button>

      <button
        type="button"
        title="Reset map to Chennai"
        aria-label="Reset map to Chennai"
        onClick={() => map.setView(CITY_CENTER, DEFAULT_ZOOM)}
        className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-[#0d1826] text-xs text-[#00D4FF] shadow-lg hover:bg-slate-800"
      >
        City
      </button>

      <button
        type="button"
        title="Fit all roads and facilities"
        aria-label="Fit all roads and facilities"
        onClick={fitAll}
        className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-[#0d1826] text-xs text-white shadow-lg hover:bg-slate-800"
      >
        Fit
      </button>
    </div>
  );
}

function MapLegend() {
  return (
    <div className="absolute bottom-5 left-4 z-[1000] max-w-[calc(100%-2rem)] rounded-xl border border-white/10 bg-[#0d1826]/95 p-3 text-xs text-slate-200 shadow-xl backdrop-blur">
      <p className="mb-2 font-semibold text-white">Map Legend</p>

      <div className="grid grid-cols-2 gap-x-4 gap-y-2">
        <span className="flex items-center gap-2">
          <span className="h-1 w-5 rounded bg-[#4ADE80]" />
          Arterial road
        </span>

        <span className="flex items-center gap-2">
          <span className="h-1 w-5 rounded bg-[#475569]" />
          Other roads
        </span>

        {Object.entries(FACILITY_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: color }}
            />
            {type.replace(/_/g, " ")}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function CityMapView({
  roads,
  facilities,
  onRoadSelect,
  selectedRoad,
}: Props) {
  const validRoads = useMemo(
    () =>
      roads.filter(
        (road) =>
          isValidCoordinate(road.node_a_lat, road.node_a_lon) &&
          isValidCoordinate(road.node_b_lat, road.node_b_lon)
      ),
    [roads]
  );

  const validFacilities = useMemo(
    () =>
      facilities.filter((facility) =>
        isValidCoordinate(facility.lat, facility.lon)
      ),
    [facilities]
  );

  return (
    <div className="relative h-full min-h-[400px] w-full overflow-hidden bg-[#0a0f1a]">
      <LeafletMap
        center={CITY_CENTER}
        zoom={DEFAULT_ZOOM}
        className="h-full w-full"
        style={{ background: "#0a0f1a" }}
      >
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a>'
          maxZoom={19}
        />

        <MapController
          roads={validRoads}
          facilities={validFacilities}
        />

        {validRoads.map((road) => {
          const positions = getRoadPositions(road);

          if (positions.length < 2) {
            return null;
          }

          const selected = selectedRoad?.id === road.id;
          const arterial = road.road_class === "arterial";

          return (
            <Polyline
              key={road.id}
              positions={positions}
              pathOptions={{
                color: selected
                  ? "#00D4FF"
                  : arterial
                    ? "#4ADE80"
                    : "#475569",
                weight: selected ? 7 : arterial ? 4 : 2,
                opacity: selected ? 1 : 0.85,
              }}
              eventHandlers={{
                click: () => onRoadSelect(road),
              }}
            >
              <Popup>
                <div className="min-w-[160px] text-sm">
                  <strong>{road.name || `Road ${road.id}`}</strong>

                  <p>Class: {road.road_class || "Not specified"}</p>

                  {road.speed_kmph != null && (
                    <p>Speed: {road.speed_kmph} km/h</p>
                  )}

                  {road.capacity_vph != null && (
                    <p>Capacity: {road.capacity_vph} vehicles/hour</p>
                  )}

                  <p className="mt-2 text-xs">
                    Click the road to select it.
                  </p>
                </div>
              </Popup>
            </Polyline>
          );
        })}

        {validFacilities.map((facility) => {
          const color =
            FACILITY_COLORS[facility.facility_type] || "#FFFFFF";

          return (
            <CircleMarker
              key={`${facility.facility_type}-${facility.id}`}
              center={[facility.lat, facility.lon]}
              radius={6}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.95,
                weight: 2,
              }}
            >
              <Popup>
                <div className="text-sm">
                  <strong>{facility.name}</strong>
                  <p className="mt-1 capitalize">
                    {facility.facility_type.replace(/_/g, " ")}
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        <MapControls />
        <MapLegend />
      </LeafletMap>

      {roads.length === 0 && facilities.length === 0 && (
        <div className="absolute left-1/2 top-1/2 z-[1000] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-white/10 bg-[#0d1826] px-5 py-4 text-center shadow-xl">
          <p className="text-sm font-semibold text-white">
            No map data available
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Check whether the backend has roads and facilities.
          </p>
        </div>
      )}

      {((roads.length > 0 && validRoads.length === 0) ||
        (facilities.length > 0 && validFacilities.length === 0)) && (
        <div className="absolute bottom-5 right-4 z-[1000] max-w-xs rounded-lg border border-amber-500/30 bg-[#0d1826] p-3 text-xs text-amber-200 shadow-lg">
          Some map data could not be displayed because its coordinates
          are invalid. Check the coordinates returned by the backend.
        </div>
      )}
    </div>
  );
}