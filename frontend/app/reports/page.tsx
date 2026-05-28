"use client";

import React, { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, PieChart, Pie, Legend } from "recharts";
import { Calendar, BarChart3, TrendingUp, ShieldAlert, Award, Clock, Loader2, ArrowRight } from "lucide-react";
import Shell from "@/components/layout/Shell";
import api from "@/lib/api";

interface TacticCount {
  tactic: string;
  count: number;
}

interface SourceIpCount {
  ip: string;
  alert_count: number;
}

interface DailyVolume {
  date: string;
  count: number;
}

interface ReportData {
  total_alerts: number;
  by_severity: { critical: number; high: number; medium: number; low: number };
  false_positive_rate: number;
  mean_triage_time_minutes: number;
  top_mitre_tactics: TacticCount[];
  top_source_ips: SourceIpCount[];
  alert_volume_by_day: DailyVolume[];
}

export default function ReportsPage() {
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Date range presets (default to last 7 days)
  const [daysRange, setDaysRange] = useState(7);

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      const toTime = new Date();
      const fromTime = new Date();
      fromTime.setDate(fromTime.getDate() - daysRange);

      const response = await api.get("/reports/summary", {
        params: {
          from_time: fromTime.toISOString(),
          to_time: toTime.toISOString()
        }
      });
      setData(response.data);
    } catch (err: any) {
      console.error("Failed to load report analytics:", err);
      setError("Failed to load SOC analytics data from PostgreSQL.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, [daysRange]);

  // Color mapping for severities
  const SEVERITY_COLORS = {
    critical: "#ef4444",
    high: "#f97316",
    medium: "#eab308",
    low: "#22c55e",
  };

  // Prepare Pie Chart data
  const severityData = data
    ? [
        { name: "Critical", value: data.by_severity.critical, color: SEVERITY_COLORS.critical },
        { name: "High", value: data.by_severity.high, color: SEVERITY_COLORS.high },
        { name: "Medium", value: data.by_severity.medium, color: SEVERITY_COLORS.medium },
        { name: "Low", value: data.by_severity.low, color: SEVERITY_COLORS.low },
      ].filter((item) => item.value > 0)
    : [];

  return (
    <Shell>
      <div className="flex flex-col gap-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-extrabold text-slate-100 uppercase tracking-wider">
              SOC Analytics & Reports
            </h1>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mt-1">
              Performance metrics, volume tracking, and MITRE ATT&CK trends
            </p>
          </div>

          {/* Date range picker */}
          <div className="flex items-center gap-2 self-end">
            <span className="text-slate-500 text-xs font-bold uppercase mr-1 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5" />
              Range:
            </span>
            {[7, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setDaysRange(days)}
                className={`
                  px-3 py-1.5 rounded text-[10px] font-bold border uppercase tracking-wider transition-all duration-155
                  ${
                    daysRange === days
                      ? "bg-blue-600 border-blue-500 text-white"
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                  }
                `}
              >
                Last {days} Days
              </button>
            ))}
          </div>
        </div>

        {loading && (
          <div className="p-20 text-center flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Compiling analytical metrics...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-950/40 border border-red-900/50 p-6 rounded-lg text-center max-w-lg mx-auto">
            <h3 className="font-bold text-red-400">Analytics Error</h3>
            <p className="text-xs text-red-300 mt-2">{error}</p>
            <button
              onClick={fetchReportData}
              className="mt-4 px-4 py-2 bg-slate-850 hover:bg-slate-750 text-xs text-slate-200 border border-slate-700/60 rounded font-semibold transition-all duration-150"
            >
              Retry Load
            </button>
          </div>
        )}

        {data && !loading && !error && (
          <div className="flex flex-col gap-6">
            
            {/* Analytical Metrics KPI row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg shadow-sm flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Incidents</span>
                  <span className="text-2xl font-extrabold text-slate-200 mt-1 block font-mono">{data.total_alerts}</span>
                </div>
                <div className="p-2.5 bg-blue-950/40 rounded border border-blue-900/40 text-blue-400">
                  <ShieldAlert className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg shadow-sm flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">False Positive Rate</span>
                  <span className="text-2xl font-extrabold text-green-400 mt-1 block font-mono">{(data.false_positive_rate * 100).toFixed(1)}%</span>
                </div>
                <div className="p-2.5 bg-green-950/40 rounded border border-green-900/40 text-green-400">
                  <Award className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg shadow-sm flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Mean Time to Triage</span>
                  <span className="text-2xl font-extrabold text-slate-200 mt-1 block font-mono">{data.mean_triage_time_minutes} m</span>
                </div>
                <div className="p-2.5 bg-slate-850 rounded border border-slate-700/50 text-slate-400">
                  <Clock className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg shadow-sm flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">FP Reduction SLA</span>
                  <span className="text-2xl font-extrabold text-blue-400 mt-1 block font-mono">60% target</span>
                </div>
                <div className="p-2.5 bg-slate-850 rounded border border-slate-700/50 text-slate-400">
                  <TrendingUp className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* Row 2: Charts Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Daily Alert Volume Trend (2 cols width) */}
              <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-5 rounded-lg shadow-md flex flex-col gap-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Alert Volume Daily Trend</span>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.alert_volume_by_day} margin={{ left: -20, right: 10, top: 10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: 9, fontFamily: "monospace" }} />
                      <YAxis stroke="#64748b" style={{ fontSize: 9, fontFamily: "monospace" }} />
                      <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                      <Area type="monotone" dataKey="count" stroke="#3b82f6" fillOpacity={1} fill="url(#colorCount)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Severity distribution Pie chart (1 col width) */}
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg shadow-md flex flex-col gap-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Severity Classification</span>
                {severityData.length === 0 ? (
                  <p className="text-xs text-slate-500 italic text-center py-20">No active alerts recorded.</p>
                ) : (
                  <div className="h-[250px] w-full flex items-center justify-center relative">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={severityData}
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {severityData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                        <Legend wrapperStyle={{ fontSize: 10 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

            </div>

            {/* Row 3: MITRE ATT&CK and Top Sources */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* MITRE Tactics Distribution */}
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg shadow-md flex flex-col gap-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Top MITRE ATT&CK Tactics</span>
                {data.top_mitre_tactics.length === 0 ? (
                  <p className="text-xs text-slate-500 italic text-center py-10">No tactics tagged.</p>
                ) : (
                  <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.top_mitre_tactics} layout="vertical" margin={{ left: 20, right: 10, top: 0, bottom: 0 }}>
                        <CartesianGrid stroke="#1e293b" horizontal={false} />
                        <XAxis type="number" stroke="#64748b" style={{ fontSize: 9 }} />
                        <YAxis dataKey="tactic" type="category" stroke="#64748b" style={{ fontSize: 9 }} width={100} />
                        <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                        <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]}>
                          {data.top_mitre_tactics.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill="#3b82f6" />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Top scanning Source IPs */}
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg shadow-md flex flex-col gap-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Top Incident Source IPs</span>
                {data.top_source_ips.length === 0 ? (
                  <p className="text-xs text-slate-500 italic text-center py-10">No scanning source IPs logged.</p>
                ) : (
                  <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.top_source_ips} margin={{ left: -20, right: 10, top: 10, bottom: 0 }}>
                        <CartesianGrid stroke="#1e293b" vertical={false} />
                        <XAxis dataKey="ip" stroke="#64748b" style={{ fontSize: 9, fontFamily: "monospace" }} />
                        <YAxis stroke="#64748b" style={{ fontSize: 9 }} />
                        <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155" }} />
                        <Bar dataKey="alert_count" fill="#f97316" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

            </div>

          </div>
        )}
      </div>
    </Shell>
  );
}
