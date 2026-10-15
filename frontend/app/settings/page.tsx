"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";

export default function SettingsPage() {
  const [role, setRole] = useState<string | null>(null);
  const [apiUrl, setApiUrl] = useState("");

  useEffect(() => {
    setApiUrl(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");
    // Role comes from the JWT issued at login; decode client-side for display only
    // (never trust this for access control — the backend enforces permissions).
    const token = localStorage.getItem("citymind_token");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setRole(payload.role);
      } catch {
        setRole(null);
      }
    }
  }, []);

  function logout() {
    localStorage.removeItem("citymind_token");
    window.location.href = "/";
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8 max-w-2xl">
        <h1 className="text-xl font-semibold mb-6">Settings</h1>

        <div className="space-y-4">
          <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
            <p className="text-xs text-slate-500 mb-1">Signed in as</p>
            <p className="text-sm font-medium">{role ? role.charAt(0).toUpperCase() + role.slice(1) : "Not signed in"}</p>
          </div>

          <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
            <p className="text-xs text-slate-500 mb-1">API Endpoint</p>
            <p className="text-sm font-mono text-slate-400">{apiUrl}</p>
          </div>

          <button
            onClick={logout}
            className="text-sm px-4 py-2 rounded-lg border border-[#EF4444]/30 text-[#EF4444]
                       hover:bg-[#EF4444]/10 transition-colors"
          >
            Sign out
          </button>
        </div>
      </main>
    </div>
  );
}