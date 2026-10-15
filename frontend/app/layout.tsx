import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CityMind — Simulate Today. Build Tomorrow.",
  description: "AI-powered Urban Digital Twin and Decision Intelligence Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#09111f] text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}