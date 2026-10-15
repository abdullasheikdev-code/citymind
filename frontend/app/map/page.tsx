"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { getRoads, getFacilities } from "@/lib/api";

const MapView = dynamic(() => import("@/components/CityMapView"), { ssr: false });

const FACILITY_TYPES = ["hospital", "school", "fire_station", "police_station", "bus_stop", "parking"];

export default function MapPage() {
  const [roads, setRoads] = useState<any[]>([]);
  const [facilities, setFacilities] = useState<any[]>([]);
  const [visibleTypes, setVisibleTypes] = useState<string[]>(FACILITY_TYPES);
  const [selectedRoad, setSelectedRoad] = useState<any | null>(null);

  useEffect(() => {
    getRoads().then(setRoads).catch(console.error);
    getFacilities().then(setFacilities).catch(console.error);
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 h-screen flex flex-col">
        <header className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
          <h1 className="text-lg font-semibold">City Map</h1>
          <div className="flex gap-2 flex-wrap">
            {FACILITY_TYPES.map((t) => (
              <button
                key={t}
                onClick={() =>
                  setVisibleTypes((prev) =>
                    prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
                  )
                }
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors
                  ${visibleTypes.includes(t)
                    ? "border-[#00D4FF]/40 bg-[#00D4FF]/10 text-[#00D4FF]"
                    : "border-white/10 text-slate-500"}`}
              >
                {t.replace("_", " ")}
              </button>
            ))}
          </div>
        </header>

        <div className="flex-1 relative">
          <MapView
            roads={roads}
            facilities={facilities.filter((f) => visibleTypes.includes(f.facility_type))}
            onRoadSelect={setSelectedRoad}
            selectedRoad={selectedRoad}
          />
        </div>

        {selectedRoad && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-[#0d1826] border
                          border-white/10 rounded-xl px-5 py-4 shadow-2xl backdrop-blur-xl">
            <p className="text-sm font-medium">{selectedRoad.name}</p>
            <p className="text-xs text-slate-400 mt-1">
              {selectedRoad.road_class} · {selectedRoad.speed_kmph} km/h · cap {selectedRoad.capacity_vph} vph
            </p>
            <a
              href={`/simulation?road_id=${selectedRoad.id}`}
              className="inline-block mt-3 text-xs px-3 py-1.5 rounded-lg bg-[#00D4FF] text-[#09111f] font-medium"
            >
              Simulate closure →
            </a>
          </div>
        )}
      </main>
    </div>
  );
}