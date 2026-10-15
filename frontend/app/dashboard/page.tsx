"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { getDashboardSummary, getInfrastructureHealth } from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<any | null>(null);
  const [health, setHealth] = useState<any | null>(null);

  useEffect(() => {
    getDashboardSummary().then(setSummary).catch(console.error);
    getInfrastructureHealth().then(setHealth).catch(console.error);
  }, []);

  const cards = summary && health ? [
    { label: "Road Segments", value: summary.total_road_segments },
    { label: "Arterial Roads", value: summary.arterial_road_segments },
    { label: "Avg Speed Limit", value: `${summary.avg_speed_limit_kmph} km/h` },
    { label: "Population Covered", value: summary.total_population_tracked.toLocaleString() },
    { label: "Hospitals", value: summary.facility_counts.hospital ?? 0 },
    { label: "Schools", value: summary.facility_counts.school ?? 0 },
    { label: "Infrastructure Health", value: `${health.infrastructure_health_score}/100` },
    { label: "Signal Coverage", value: `${health.signal_coverage_pct}%` },
  ] : [];

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-xl font-semibold mb-6">City Dashboard</h1>
        <div className="grid grid-cols-4 gap-4">
          {cards.map(({ label, value }) => (
            <div key={label} className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
              <p className="text-xs text-slate-500 mb-2">{label}</p>
              <p className="text-2xl font-semibold text-[#00D4FF]">{value}</p>
            </div>
          ))}
        </div>

        {health && health.coverage_gaps.length > 0 && (
          <div className="mt-6 bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded-xl p-5">
            <h3 className="text-sm font-medium text-[#F59E0B] mb-2">Coverage Gaps Detected</h3>
            {health.coverage_gaps.map((g: any) => (
              <p key={g.facility_type} className="text-sm text-slate-300">
                No {g.facility_type.replace("_", " ")} access: {g.uncovered_zones.join(", ")}
              </p>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}