"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { login, register, setAuthToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("planner");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = mode === "login"
        ? await login(email, password)
        : await register(email, password, role);
      setAuthToken(res.access_token);
      router.push("/dashboard");
    } catch (e: any) {
      setError(e.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#09111f] text-slate-100 flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <Image src="/logo.svg" alt="CityMind" width={36} height={36} />
          <span className="font-semibold tracking-tight text-lg">CITYMIND</span>
        </div>

        <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-6 backdrop-blur-xl">
          <div className="flex gap-2 mb-6 text-sm">
            <button
              onClick={() => setMode("login")}
              className={`flex-1 py-2 rounded-lg transition-colors ${
                mode === "login" ? "bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/20" : "text-slate-500"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setMode("register")}
              className={`flex-1 py-2 rounded-lg transition-colors ${
                mode === "register" ? "bg-[#00D4FF]/10 text-[#00D4FF] border border-[#00D4FF]/20" : "text-slate-500"
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm
                         focus:outline-none focus:border-[#00D4FF]/50"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm
                         focus:outline-none focus:border-[#00D4FF]/50"
            />

            {mode === "register" && (
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm"
              >
                <option value="viewer">Viewer — read only</option>
                <option value="planner">Planner — run simulations</option>
                <option value="admin">Admin — full access</option>
              </select>
            )}

            {error && (
              <p className="text-xs text-[#EF4444] bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-[#00D4FF] text-[#09111f] text-sm font-medium
                         disabled:opacity-40 transition-opacity"
            >
              {loading ? "…" : mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-600 mt-6">
          Simulate Today. Build Tomorrow.
        </p>
      </div>
    </main>
  );
}