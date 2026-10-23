"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import {
  simulateRoadClosure,
  type SimulationResponse,
  reportDownloadUrl,
} from "@/lib/api";
import { RouteDelayChart } from "@/components/RouteDelayChart";

function SimulationContent() {
  const params = useSearchParams();
  const initialRoadId = params.get("road_id");

  const [roadId, setRoadId] = useState(initialRoadId || "");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runSimulation() {
    const parsedRoadId = Number(roadId);

    if (!roadId.trim() || !Number.isInteger(parsedRoadId) || parsedRoadId <= 0) {
      setError("Please enter a valid positive Road ID.");
      setResult(null);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await simulateRoadClosure(parsedRoadId);
      console.log("SIMULATION RESPONSE:", JSON.stringify(response, null, 2));
      setResult(response);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to run the simulation. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  const metrics = result?.result.metrics;

  const metricCards = result
    ? [
        {
          label: "Hospital delay — affected zones",
          value: metrics?.avg_hospital_route_delay_pct,
          suffix: "%",
        },
        {
          label: "Hospital delay — all zones",
          value: metrics?.avg_hospital_route_delay_pct_all_zones,
          suffix: "%",
        },
        {
          label: "School delay — affected zones",
          value: metrics?.avg_school_route_delay_pct,
          suffix: "%",
        },
        {
          label: "School delay — all zones",
          value: metrics?.avg_school_route_delay_pct_all_zones,
          suffix: "%",
        },
        {
          label: "Zones with increased hospital travel",
          value: metrics?.zones_with_increased_hospital_travel,
          suffix: "",
        },
        {
          label: "Zones with increased school travel",
          value: metrics?.zones_with_increased_school_travel,
          suffix: "",
        },
        {
          label: "Maximum ambulance delay",
          value: metrics?.max_ambulance_delay_min,
          suffix: " min",
        },
        {
          label: "Zones cut off entirely",
          value: metrics?.zones_cut_off_entirely,
          suffix: "",
        },
      ]
    : [];

  return (
    <div className="flex min-h-screen bg-[#09111f] text-white">
      <Sidebar />

      <main className="min-w-0 flex-1 p-5 sm:p-8">
        <div className="mx-auto max-w-6xl">
          <header className="mb-7">
            <h1 className="text-2xl font-semibold tracking-tight">
              Simulation — Road Closure
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Analyze how closing a road changes travel times to hospitals
              and schools. Route calculations come from the road-network
              graph engine.
            </p>
          </header>

          <section className="mb-8 rounded-xl border border-white/10 bg-white/[0.03] p-5">
            <label
              htmlFor="roadId"
              className="mb-2 block text-sm font-medium text-slate-300"
            >
              Road ID
            </label>

            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                id="roadId"
                type="number"
                min="1"
                step="1"
                value={roadId}
                onChange={(event) => setRoadId(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !loading) {
                    void runSimulation();
                  }
                }}
                placeholder="Enter Road ID"
                className="w-full rounded-lg border border-white/10 bg-[#0d1826] px-4 py-3 text-sm text-white outline-none transition focus:border-[#00D4FF]/60 sm:w-56"
              />

              <button
                type="button"
                onClick={() => void runSimulation()}
                disabled={loading || !roadId.trim()}
                className="rounded-lg bg-[#00D4FF] px-6 py-3 text-sm font-semibold text-[#09111f] transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "Simulating..." : "Run Simulation"}
              </button>
            </div>

            <p className="mt-3 text-xs text-slate-500">
              Enter an existing road ID from your city road network.
            </p>
          </section>

          {error && (
            <div
              role="alert"
              className="mb-6 rounded-lg border border-red-400/30 bg-red-400/10 px-4 py-3 text-sm text-red-300"
            >
              {error}
            </div>
          )}

          {loading && (
            <div
              role="status"
              className="mb-6 rounded-lg border border-white/10 bg-white/[0.03] p-5 text-sm text-slate-300"
            >
              Calculating route impacts and generating the explanation...
            </div>
          )}

          {result && (
            <div className="space-y-6">
              <section>
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold">
                      Simulation Results
                    </h2>
                    <p className="mt-1 text-sm text-slate-400">
                      {result.result.input.road_name
                        ? `${result.result.input.road_name} · `
                        : ""}
                      Road ID {result.result.input.road_id}
                    </p>
                  </div>

                  <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-300">
                    Scenario #{result.scenario_id}
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  {metricCards.map((metric) => {
                    const missing = metric.value == null;
                    const numericValue = Number(metric.value);

                    return (
                      <div
                        key={metric.label}
                        className="rounded-xl border border-white/10 bg-white/[0.03] p-4"
                      >
                        <p className="mb-3 text-xs leading-5 text-slate-400">
                          {metric.label}
                        </p>

                        <p className="text-2xl font-semibold text-[#00D4FF]">
                          {missing || !Number.isFinite(numericValue)
                            ? "N/A"
                            : `${numericValue.toFixed(
                                metric.suffix === "%" || metric.suffix === " min"
                                  ? 1
                                  : 0
                              )}${metric.suffix}`}
                        </p>
                      </div>
                    );
                  })}
                </div>

                {(metrics?.avg_hospital_route_delay_pct_all_zones == null ||
                  metrics?.avg_school_route_delay_pct_all_zones == null) && (
                  <p className="mt-3 text-xs leading-5 text-amber-300">
                    The all-zone averages are not present in this API response.
                    Apply the backend metric update and rerun the simulation
                    to display them.
                  </p>
                )}
              </section>

              <section className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
                <h2 className="mb-3 text-base font-semibold text-slate-200">
                  AI Explanation
                </h2>
                <p className="whitespace-pre-line text-sm leading-7 text-slate-300">
                  {result.explanation || "No explanation was returned."}
                </p>
              </section>

              {result.result.hospital_route_detail && (
                <RouteDelayChart data={result.result.hospital_route_detail} />
              )}

              {result.result.school_route_detail &&
                result.result.school_route_detail.length > 0 && (
                  <RouteDelayChart data={result.result.school_route_detail} />
                )}

              {result.result.recommendation && (
                <section className="rounded-xl border border-emerald-400/20 bg-emerald-400/[0.05] p-5">
                  <h2 className="mb-3 text-base font-semibold text-emerald-300">
                    Recommended Detour
                  </h2>
                  <p className="text-sm leading-7 text-slate-300">
                    {result.result.recommendation.text}
                  </p>

                  {result.result.recommendation.detour_roads.length > 0 && (
                    <div className="mt-4">
                      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
                        Suggested roads
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {result.result.recommendation.detour_roads.map(
                          (road, index) => (
                            <span
                              key={`${road}-${index}`}
                              className="rounded-md border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300"
                            >
                              {index + 1}. {road}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}
                </section>
              )}

              <section className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
                <h2 className="mb-2 text-base font-semibold text-slate-200">
                  Calculation Method
                </h2>
                <p className="text-sm leading-7 text-slate-400">
                  {result.result.basis.method}
                </p>
                <p className="mt-3 text-xs leading-5 text-slate-500">
                  The simulation recalculates shortest routes after excluding
                  the selected road. Results depend on the roads, facilities,
                  and population zones in your database.
                </p>
              </section>

              <div className="flex flex-wrap gap-3">
                <a
                  href={reportDownloadUrl(result.scenario_id)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center rounded-lg border border-white/15 px-4 py-3 text-sm font-medium text-slate-200 transition hover:border-cyan-400/40 hover:text-cyan-300"
                >
                  Download PDF Report
                  <span className="ml-2" aria-hidden="true">
                    ↗
                  </span>
                </a>

                <button
                  type="button"
                  onClick={() => {
                    setResult(null);
                    setError(null);
                  }}
                  className="rounded-lg border border-white/10 px-4 py-3 text-sm text-slate-300 transition hover:bg-white/[0.05]"
                >
                  Clear Results
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default function SimulationPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#09111f] p-8 text-sm text-slate-400">
          Loading simulation...
        </div>
      }
    >
      <SimulationContent />
    </Suspense>
  );
}