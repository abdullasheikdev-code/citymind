"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

import type { RouteDetail } from "@/lib/api";

interface RouteDelayChartProps {
  data: RouteDetail[];
}

interface ChartData {
  zone: string;
  fullZone: string;
  delay: number;
}

export function RouteDelayChart({ data }: RouteDelayChartProps) {
  const chartData: ChartData[] = data
    .filter(
      (item) =>
        typeof item.delta_pct === "number" &&
        Number.isFinite(item.delta_pct)
    )
    .map((item) => ({
      zone:
        item.zone.length > 18
          ? `${item.zone.slice(0, 18)}…`
          : item.zone,
      fullZone: item.zone,
      delay: item.delta_pct as number,
    }));

  if (chartData.length === 0) {
    return (
      <section className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
        <h3 className="mb-2 text-sm font-semibold text-slate-200">
          Route Delay by Zone
        </h3>
        <p className="text-sm text-slate-400">
          No route-delay data is available for this simulation.
        </p>
      </section>
    );
  }

  const allZero = chartData.every((item) => item.delay === 0);

  const minDelay = Math.min(0, ...chartData.map((item) => item.delay));
  const maxDelay = Math.max(0, ...chartData.map((item) => item.delay));

  // Give an all-zero chart a visible scale without inventing delay values.
  const padding = allZero
    ? 1
    : Math.max((maxDelay - minDelay) * 0.15, 0.5);

  const yMin = minDelay < 0 ? minDelay - padding : 0;
  const yMax = maxDelay > 0 ? maxDelay + padding : allZero ? 1 : 0.5;

  return (
    <section className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">
            Route Delay by Zone
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Percentage change in route travel time
          </p>
        </div>

        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            allZero
              ? "border border-emerald-400/20 bg-emerald-400/10 text-emerald-300"
              : "border border-cyan-400/20 bg-cyan-400/10 text-cyan-300"
          }`}
        >
          {allZero ? "No reported delay" : `${chartData.length} zones`}
        </span>
      </div>

      {allZero && (
        <div className="mb-4 rounded-lg border border-emerald-400/20 bg-emerald-400/5 p-3">
          <p className="text-sm font-medium text-emerald-300">
            No route-delay increase reported
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-400">
            All available zone values are 0%. The chart below preserves the
            actual data; no artificial delay values have been added.
          </p>
        </div>
      )}

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 12, right: 12, bottom: 55, left: 4 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#ffffff12"
              vertical={false}
            />

            <XAxis
              dataKey="zone"
              interval={0}
              angle={-30}
              textAnchor="end"
              height={75}
              tick={{ fontSize: 10, fill: "#94a3b8" }}
              axisLine={{ stroke: "#ffffff20" }}
              tickLine={false}
            />

            <YAxis
              type="number"
              domain={[yMin, yMax]}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickFormatter={(value: number) => `${value}%`}
              axisLine={false}
              tickLine={false}
              width={48}
            />

            <ReferenceLine y={0} stroke="#94a3b8" strokeOpacity={0.6} />

            <Tooltip
              cursor={{ fill: "#ffffff08" }}
              contentStyle={{
                background: "#0d1826",
                border: "1px solid #ffffff25",
                borderRadius: 8,
                color: "#e2e8f0",
                fontSize: 12,
              }}
              labelFormatter={(_, payload) =>
                payload?.[0]?.payload?.fullZone ?? ""
              }
              formatter={(value) => [
                `${Number(value).toFixed(2)}%`,
                "Route delay",
              ]}
            />

            <Bar
              dataKey="delay"
              name="Route delay"
              fill="#00D4FF"
              radius={[4, 4, 0, 0]}
              maxBarSize={36}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-2 text-xs text-slate-500">
        Positive values indicate increased travel time; negative values
        indicate reduced travel time.
      </p>
    </section>
  );
}