"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Map, Activity, History, Building2,
  ShieldAlert, FileText, BarChart3, Bot, Settings,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/map", label: "City Map", icon: Map },
  { href: "/simulation", label: "Simulation", icon: Activity },
  { href: "/scenarios", label: "Scenario History", icon: History },
  { href: "/infrastructure", label: "Infrastructure", icon: Building2 },
  { href: "/emergency", label: "Emergency Planning", icon: ShieldAlert },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/assistant", label: "AI Assistant", icon: Bot },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 border-r border-white/10
                       bg-white/[0.02] backdrop-blur-xl flex flex-col">
      <div className="px-5 py-6 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00D4FF] to-[#4ADE80]" />
          <span className="font-semibold tracking-tight text-lg">CITYMIND</span>
        </div>
        <p className="text-xs text-slate-400 mt-1">Simulate Today. Build Tomorrow.</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors
                ${active
                  ? "bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/20"
                  : "text-slate-400 hover:text-slate-100 hover:bg-white/5"}`}
            >
              <Icon size={17} strokeWidth={1.75} />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}