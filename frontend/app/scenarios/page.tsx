"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { listScenarios, compareScenarios, ScenarioSummary } from "@/lib/api";

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [comparison, setComparison] = useState<any | null>(null);

  useEffect(() => {
    listScenarios().then(setScenarios).catch(console.error);
  }, []);

  function toggleSelect(id: number) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 2 ? [...prev, id] : [prev[1], id]
    );
  }

  async function runCompare() {
    if (selected.length !== 2) return;
    const res = await compareScenarios(selected[0], selected[1]);
    setComparison(res);
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-5xl">
        <h1 className="text-xl font-semibold mb-1">Scenario History</h1>
        <p className="text-sm text-slate-400 mb-6">Select two scenarios of the same type to compare.</p>

        <div className="space-y-2 mb-6">
          {scenarios.map((s) => (
            <label
              key={s.id}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-colors
                ${selected.includes(s.id) ? "border-[#00D4FF]/50 bg-[#00D4FF]/5" : "border-white/10 hover:border-white/20"}`}
            >
              <input type="checkbox" checked={selected.includes(s.id)} onChange={() => toggleSelect(s.id)} />
              <span className="text-sm font-medium">#{s.id}</span>
              <span className="text-sm text-slate-400">{s.scenario_type.replace("_", " ")}</span>
              <span className="text-xs text-slate-600 ml-auto">{new Date(s.created_at).toLocaleString()}</span>
            </label>
          ))}
        </div>

        <button
          onClick={runCompare}
          disabled={selected.length !== 2}
          className="px-5 py-2.5 rounded-lg bg-[#00D4FF] text-[#09111f] text-sm font-medium disabled:opacity-40"
        >
          Compare Selected
        </button>

        {comparison && (
          <div className="mt-8 border border-white/10 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-white/5">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Metric</th>
                  <th className="text-left px-4 py-3 font-medium text-[#00D4FF]">Option A (#{comparison.option_a.id})</th>
                  <th className="text-left px-4 py-3 font-medium text-[#4ADE80]">Option B (#{comparison.option_b.id})</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(comparison.metric_comparison).map(([key, val]: [string, any]) => (
                  <tr key={key} className="border-t border-white/5">
                    <td className="px-4 py-3 text-slate-400">{key.replace(/_/g, " ")}</td>
                    <td className="px-4 py-3">{String(val.option_a)}</td>
                    <td className="px-4 py-3">{String(val.option_b)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}