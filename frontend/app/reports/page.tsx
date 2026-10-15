"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { listScenarios, reportDownloadUrl, ScenarioSummary } from "@/lib/api";

export default function ReportsPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);

  useEffect(() => {
    listScenarios().then(setScenarios).catch(console.error);
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-4xl">
        <h1 className="text-xl font-semibold mb-1">Reports</h1>
        <p className="text-sm text-slate-400 mb-6">
          Download a PDF report for any past simulation — Executive Summary, Predicted
          Impacts, Affected Areas, Risk Level, and Recommendation.
        </p>

        {scenarios.length === 0 && (
          <p className="text-sm text-slate-500">
            No simulations have been run yet. Run one from the Simulation page first.
          </p>
        )}

        <div className="space-y-2">
          {scenarios.map((s) => (
            <div
              key={s.id}
              className="flex items-center justify-between px-4 py-3 rounded-lg border border-white/10 hover:border-white/20"
            >
              <div>
                <p className="text-sm font-medium">
                  #{s.id} — {s.scenario_type.replace("_", " ")}
                </p>
                <p className="text-xs text-slate-500">{new Date(s.created_at).toLocaleString()}</p>
              </div>
              <a
                href={reportDownloadUrl(s.id)}
                target="_blank"
                className="text-xs px-3 py-1.5 rounded-lg bg-[#00D4FF] text-[#09111f] font-medium"
              >
                Download PDF
              </a>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}