"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { getFacilities } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const FACILITY_TYPES = ["hospital", "school", "fire_station", "police_station", "bus_stop", "parking"];

export default function InfrastructurePage() {
  const [facilities, setFacilities] = useState<any[]>([]);
  const [filterType, setFilterType] = useState<string>("all");
  const [form, setForm] = useState({ facility_type: "hospital", name: "", lat: "", lon: "", capacity: "" });
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    getFacilities().then(setFacilities).catch(console.error);
  }

  useEffect(refresh, []);

  async function addFacility(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const token = localStorage.getItem("citymind_token");
      const res = await fetch(`${API_BASE}/city/facilities`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          facility_type: form.facility_type,
          name: form.name,
          lat: parseFloat(form.lat),
          lon: parseFloat(form.lon),
          capacity: form.capacity ? parseInt(form.capacity, 10) : null,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to add facility");
      setForm({ facility_type: "hospital", name: "", lat: "", lon: "", capacity: "" });
      refresh();
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function deleteFacility(id: number) {
    const token = localStorage.getItem("citymind_token");
    await fetch(`${API_BASE}/city/facilities/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    refresh();
  }

  const filtered = filterType === "all" ? facilities : facilities.filter((f) => f.facility_type === filterType);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-5xl">
        <h1 className="text-xl font-semibold mb-1">Infrastructure</h1>
        <p className="text-sm text-slate-400 mb-6">
          Add, inspect, or remove hospitals, schools, stations, and other city facilities.
          Changes snap to the nearest road intersection for routing purposes.
        </p>

        <form onSubmit={addFacility} className="bg-white/[0.03] border border-white/10 rounded-xl p-5 mb-8">
          <h3 className="text-sm font-medium mb-4 text-slate-300">Add Facility</h3>
          <div className="grid grid-cols-5 gap-3">
            <select
              value={form.facility_type}
              onChange={(e) => setForm({ ...form, facility_type: e.target.value })}
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm col-span-1"
            >
              {FACILITY_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace("_", " ")}</option>
              ))}
            </select>
            <input
              placeholder="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm col-span-2"
            />
            <input
              placeholder="Lat"
              value={form.lat}
              onChange={(e) => setForm({ ...form, lat: e.target.value })}
              required
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm"
            />
            <input
              placeholder="Lon"
              value={form.lon}
              onChange={(e) => setForm({ ...form, lon: e.target.value })}
              required
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div className="flex items-center gap-3 mt-3">
            <input
              placeholder="Capacity (optional)"
              value={form.capacity}
              onChange={(e) => setForm({ ...form, capacity: e.target.value })}
              className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm w-48"
            />
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-[#00D4FF] text-[#09111f] text-sm font-medium"
            >
              Add
            </button>
          </div>
          {error && <p className="text-xs text-[#EF4444] mt-2">{error}</p>}
        </form>

        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setFilterType("all")}
            className={`text-xs px-3 py-1.5 rounded-full border ${filterType === "all" ? "border-[#00D4FF]/40 bg-[#00D4FF]/10 text-[#00D4FF]" : "border-white/10 text-slate-500"}`}
          >
            all
          </button>
          {FACILITY_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`text-xs px-3 py-1.5 rounded-full border ${filterType === t ? "border-[#00D4FF]/40 bg-[#00D4FF]/10 text-[#00D4FF]" : "border-white/10 text-slate-500"}`}
            >
              {t.replace("_", " ")}
            </button>
          ))}
        </div>

        <div className="border border-white/10 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-white/5">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Name</th>
                <th className="text-left px-4 py-3 font-medium">Type</th>
                <th className="text-left px-4 py-3 font-medium">Capacity</th>
                <th className="text-left px-4 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((f) => (
                <tr key={f.id} className="border-t border-white/5">
                  <td className="px-4 py-3">{f.name}</td>
                  <td className="px-4 py-3 text-slate-400">{f.facility_type.replace("_", " ")}</td>
                  <td className="px-4 py-3 text-slate-400">{f.capacity ?? "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => deleteFacility(f.id)}
                      className="text-xs text-[#EF4444] hover:underline"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}