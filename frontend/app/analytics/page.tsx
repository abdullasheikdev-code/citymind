"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Sidebar } from "@/components/Sidebar";
import { getScenarioTrends, getInfrastructureHealth, getEmergencyCoverage } from "@/lib/api";

export default function AnalyticsPage() {
  const [trends, setTrends] = useState<any | null>(null);
  const [health, setHealth] = useState<any | null>(null);
  const [emergency, setEmergency] = useState<any | null>(null);

  useEffect(() => {
    getScenarioTrends().then(setTrends).catch(console.error);
    getInfrastructureHealth().then(setHealth).catch(console.error);
    getEmergencyCoverage().then(setEmergency).catch(console.error);
  }, []);

  const trendChartData = trends
    ? Object.entries(trends.by_type || {}).map(([type, count]) => ({ type: type.replace("_", " "), count }))
    : [];

  const responseChartData = emergency
    ? emergency.zone_detail
        .map((z: any) => ({ zone: z.zone.length > 12 ? z.zone.slice(0, 12) + "…" : z.zone, fire: z.fire_response_min }))
        .sort((a: any, b: any) => b.fire - a.fire)
        .slice(0, 8)
    : [];

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-5xl">
        <h1 className="text-xl font-semibold mb-1">Analytics</h1>
        <p className="text-sm text-slate-400 mb-6">
          Trends and infrastructure metrics, computed from real scenario history and the road network.
        </p>

        {health && (
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
              <p className="text-xs text-slate-500 mb-1">Infrastructure Health</p>
              <p className="text-2xl font-semibold text-[#00D4FF]">{health.infrastructure_health_score}/100</p>
            </div>
            <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
              <p className="text-xs text-slate-500 mb-1">Signal Coverage</p>
              <p className="text-2xl font-semibold text-[#00D4FF]">{health.signal_coverage_pct}%</p>
            </div>
            <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
              <p className="text-xs text-slate-500 mb-1">Arterial Road Share</p>
              <p className="text-2xl font-semibold text-[#00D4FF]">{health.arterial_road_pct}%</p>
            </div>
          </div>
        )}

        {trends && trends.total_scenarios_run > 0 ? (
          <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5 mb-8">
            <h3 className="text-sm font-medium mb-4 text-slate-300">Simulations Run by Type</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis dataKey="type" tick={{ fontSize: 11, fill: "#64748b" }} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} allowDecimals={false} />
                <Tooltip contentStyle={{ background: "#0d1826", border: "1px solid #ffffff1a", borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="count" fill="#4ADE80" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5 mb-8">
            <p className="text-sm text-slate-500">
              No simulations run yet — this chart populates as planners use the system.
            </p>
          </div>
        )}

        {responseChartData.length > 0 && (
          <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
            <h3 className="text-sm font-medium mb-4 text-slate-300">Slowest Fire Response Zones</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={responseChartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} unit=" min" />
                <YAxis dataKey="zone" type="category" width={100} tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip contentStyle={{ background: "#0d1826", border: "1px solid #ffffff1a", borderRadius: 8, fontSize: 12 }} />
                <Bar dataKey="fire" fill="#F59E0B" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </main>
    </div>
  );
}