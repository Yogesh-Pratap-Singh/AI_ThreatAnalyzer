"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Shield, LayoutDashboard, BarChart3, LogOut, Radio, Database, Activity, User as UserIcon } from "lucide-react";
import api from "@/lib/api";

interface ShellProps {
  children: React.ReactNode;
}

export default function Shell({ children }: ShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<{ full_name: string; role: string } | null>(null);

  useEffect(() => {
    // Verify authentication and retrieve user details
    const fetchMe = async () => {
      try {
        const response = await api.get("/auth/me");
        setCurrentUser(response.data);
      } catch (err) {
        console.error("Auth check failed:", err);
        router.push("/login");
      }
    };
    fetchMe();
  }, [router]);

  const handleSignOut = async () => {
    try {
      await api.post("/auth/logout");
      router.push("/login");
    } catch (err) {
      console.error("Logout failed:", err);
      router.push("/login");
    }
  };

  const navItems = [
    { label: "Alerts Queue", href: "/dashboard", icon: LayoutDashboard },
    { label: "SOC Analytics", href: "/reports", icon: BarChart3 },
  ];

  return (
    <div className="flex min-h-screen bg-[#0f172a] text-slate-100 overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-60 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 relative z-20">
        <div className="flex flex-col gap-6 p-5">
          {/* Logo */}
          <div className="flex items-center gap-2.5 px-1 py-1">
            <div className="w-8 h-8 rounded bg-blue-600/10 border border-blue-500/30 flex items-center justify-center">
              <Shield className="w-4 h-4 text-blue-500" />
            </div>
            <span className="font-bold text-sm tracking-wide text-slate-200">
              ThreatAnalyzer
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-col gap-1.5 mt-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-3 py-2.5
                    rounded-lg text-xs font-semibold tracking-wide
                    transition-all duration-150
                    ${
                      isActive
                        ? "bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-inner"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent"
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User profile & System Status */}
        <div className="flex flex-col gap-4 p-5 border-t border-slate-800 bg-slate-900/60">
          {/* Active User */}
          {currentUser && (
            <div className="flex items-center gap-2.5 px-1">
              <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
                <UserIcon className="w-3.5 h-3.5 text-slate-400" />
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-[11px] font-bold text-slate-300 truncate leading-none">
                  {currentUser.full_name}
                </span>
                <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 mt-1">
                  {currentUser.role}
                </span>
              </div>
            </div>
          )}

          {/* System Health Indicators */}
          <div className="flex flex-col gap-2 pt-2 border-t border-slate-800/60 text-[9px] font-bold tracking-wider uppercase text-slate-500">
            <span className="flex items-center gap-1.5">
              <Database className="w-3 h-3 text-green-400" />
              Postgres: <span className="text-slate-400">16.8 ok</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Activity className="w-3 h-3 text-green-400" />
              Ingestion: <span className="text-slate-400">Healthy</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Radio className="w-3 h-3 text-green-400 animate-pulse" />
              Live Feed: <span className="text-slate-450">Streaming</span>
            </span>
          </div>

          {/* Log Out */}
          <button
            onClick={handleSignOut}
            className="flex items-center justify-center gap-2 px-3 py-2 mt-2 bg-slate-800 hover:bg-slate-750 border border-slate-700/50 hover:text-red-400 rounded-lg text-xs font-semibold transition-all duration-150 active:scale-97 text-slate-400"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-[#0f172a] relative z-10">
        {/* Top Header */}
        <header className="h-14 border-b border-slate-850 px-6 flex items-center justify-between bg-slate-900/40 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-ping" />
            <span className="text-[10px] font-bold text-slate-405 uppercase tracking-widest font-mono">
              Live SOC Console Active
            </span>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            Local Time: {new Date().toLocaleTimeString()}
          </span>
        </header>

        {/* Scrollable content container */}
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-6xl mx-auto animate-fade-in">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
