import Link from "next/link";
import Image from "next/image";
import {
  Boxes, BrainCircuit, TrendingUp, FlaskConical, Map as MapIcon, Sparkles,
} from "lucide-react";

const FEATURES = [
  { icon: Boxes, title: "Digital Twin", desc: "A living model of the city's roads, facilities, and population — kept in sync with real infrastructure data." },
  { icon: BrainCircuit, title: "AI Reasoning", desc: "Every recommendation is explained in plain language, grounded in the exact numbers the simulation computed." },
  { icon: TrendingUp, title: "Impact Analysis", desc: "Traffic delay, emergency response time, and coverage changes — computed from the road network, not guessed." },
  { icon: FlaskConical, title: "Scenario Simulation", desc: "Model road closures, new facilities, accidents, and more before committing to a real-world decision." },
  { icon: MapIcon, title: "Interactive Maps", desc: "Click any road or facility to inspect it, move it, or simulate the effect of changing it." },
  { icon: Sparkles, title: "Decision Intelligence", desc: "Compare options side by side with the same rigor a traffic engineer would apply, at planning speed." },
];

const STATS = [
  { value: "84", label: "road segments modeled" },
  { value: "12", label: "population zones tracked" },
  { value: "8", label: "simulation types supported" },
  { value: "100%", label: "explainable, no black-box numbers" },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[#09111f] text-slate-100">
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(0,212,255,0.08),transparent_50%)]" />
        <div className="relative max-w-6xl mx-auto px-6 pt-8 pb-24">
          <div className="flex items-center gap-2 mb-16">
            <Image src="/logo.svg" alt="CityMind" width={36} height={36} />
            <span className="font-semibold tracking-tight">CITYMIND</span>
          </div>

          <div className="max-w-2xl">
            <p className="text-sm text-[#00D4FF] font-medium mb-4 tracking-wide">
              SIMULATE TODAY. BUILD TOMORROW.
            </p>
            <h1 className="text-5xl font-semibold leading-tight tracking-tight mb-6">
              Build Better Cities<br />Before Building Them.
            </h1>
            <p className="text-lg text-slate-400 leading-relaxed mb-10">
              Use AI to simulate infrastructure decisions before spending millions
              in the real world. Close a road, place a hospital, or model an
              accident — see the real, computed impact before it happens.
            </p>
            <div className="flex gap-4">
              <Link
                href="/dashboard"
                className="px-6 py-3 rounded-lg bg-[#00D4FF] text-[#09111f] font-medium
                           hover:bg-[#00D4FF]/90 transition-colors"
              >
                Launch Simulator
              </Link>
              <button className="px-6 py-3 rounded-lg border border-white/15 text-slate-300
                                  hover:border-white/30 transition-colors">
                Watch Demo
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-white/10 bg-white/[0.02]">
        <div className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-4 gap-8">
          {STATS.map((s) => (
            <div key={s.label}>
              <p className="text-3xl font-semibold text-[#00D4FF]">{s.value}</p>
              <p className="text-sm text-slate-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-24">
        <h2 className="text-2xl font-semibold mb-2">Everything a planning team needs</h2>
        <p className="text-slate-400 mb-12">From first idea to defensible decision.</p>

        <div className="grid grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="p-6 rounded-2xl border border-white/10 bg-white/[0.02]
                         backdrop-blur-xl hover:border-[#00D4FF]/30 transition-colors"
            >
              <Icon className="text-[#00D4FF] mb-4" size={24} strokeWidth={1.5} />
              <h3 className="font-medium mb-2">{title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-white/10">
        <div className="max-w-6xl mx-auto px-6 py-10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Image src="/logo.svg" alt="CityMind" width={24} height={24} />
            <span className="text-sm text-slate-500">CityMind — Urban Digital Twin Platform</span>
          </div>
          <p className="text-sm text-slate-600">Simulate Today. Build Tomorrow.</p>
        </div>
      </footer>
    </main>
  );
}