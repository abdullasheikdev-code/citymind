"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { getEmergencyCoverage } from "@/lib/api";

export default function EmergencyPlanningPage() {
  const [coverage, setCoverage] = useState<any | null>(null);

  useEffect(() => {
    getEmergencyCoverage().then(setCoverage).catch(console.error);
  }, []);

  if (!coverage) return null;

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-4xl">
        <h1 className="text-xl font-semibold mb-1">Emergency Planning</h1>
        <p className="text-sm text-slate-400 mb-6">
          Real shortest-path response times, target: {coverage.response_target_min} min.
        </p>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
            <p className="text-xs text-slate-500 mb-1">Avg Fire Response</p>
            <p className="text-2xl font-semibold text-[#00D4FF]">{coverage.avg_fire_response_min} min</p>
          </div>
          <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
            <p className="text-xs text-slate-500 mb-1">Avg Police Response</p>
            <p className="text-2xl font-semibold text-[#00D4FF]">{coverage.avg_police_response_min} min</p>
          </div>
          <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
            <p className="text-xs text-slate-500 mb-1">Worst Fire Response</p>
            <p className="text-2xl font-semibold text-[#F59E0B]">{coverage.worst_fire_response_min} min</p>
          </div>
        </div>

        {coverage.zones_exceeding_target.length > 0 && (
          <div className="mb-6 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl p-4">
            <p className="text-sm text-[#EF4444]">
              Zones exceeding target: {coverage.zones_exceeding_target.join(", ")}
            </p>
          </div>
        )}

        <div className="border border-white/10 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-white/5">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Zone</th>
                <th className="text-left px-4 py-3 font-medium">Population</th>
                <th className="text-left px-4 py-3 font-medium">Fire (min)</th>
                <th className="text-left px-4 py-3 font-medium">Police (min)</th>
              </tr>
            </thead>
            <tbody>
              {coverage.zone_detail.map((z: any) => (
                <tr key={z.zone} className="border-t border-white/5">
                  <td className="px-4 py-3">{z.zone}</td>
                  <td className="px-4 py-3 text-slate-400">{z.population.toLocaleString()}</td>
                  <td className={`px-4 py-3 ${z.fire_response_min > coverage.response_target_min ? "text-[#EF4444]" : "text-slate-300"}`}>
                    {z.fire_response_min}
                  </td>
                  <td className="px-4 py-3 text-slate-300">{z.police_response_min}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}