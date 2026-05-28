"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, AlertOctagon, AlertTriangle, AlertCircle, Info, Filter, Search, RefreshCw, Layers, Loader2 } from "lucide-react";
import Shell from "@/components/layout/Shell";
import SeverityBadge from "@/components/ui/SeverityBadge";
import StatusBadge from "@/components/ui/StatusBadge";
import MitreBadge from "@/components/ui/MitreBadge";
import api, { API_URL } from "@/lib/api";

interface Alert {
  id: string;
  title: string;
  severity: string;
  severity_score: number;
  source_ip: string | null;
  dest_ip: string | null;
  event_type: string;
  mitre_tactic: string | null;
  mitre_technique_id: string | null;
  status: string;
  event_count: number;
  first_seen_at: string;
  last_seen_at: string;
  created_at: string;
  isNew?: boolean; // UI flag for pulsing animation
}

export default function DashboardPage() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters State
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("open");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // SSE ref to prevent multiple connections
  const sseRef = useRef<EventSource | null>(null);

  // Fetch initial alerts
  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      // Query L1 API
      const response = await api.get("/alerts", {
        params: {
          severity: severityFilter === "all" ? undefined : severityFilter,
          status: statusFilter === "all" ? undefined : statusFilter,
        }
      });
      setAlerts(response.data.alerts || []);
    } catch (err) {
      console.error("Failed to fetch alerts:", err);
      setError("Failed to sync alerts with database. Reconnecting...");
    } finally {
      setLoading(false);
    }
  };

  // Sync on filter changes
  useEffect(() => {
    fetchAlerts();
  }, [severityFilter, statusFilter]);

  // Set up SSE Client-Side Connection
  useEffect(() => {
    // Only connect if user is authenticated (cookies exist)
    const connectSSE = () => {
      if (sseRef.current) {
        sseRef.current.close();
      }

      // Explicitly set withCredentials on EventSource via polyfill or standard browser connection
      const es = new EventSource(`${API_URL}/alerts/stream`, {
        withCredentials: true
      } as any);

      es.addEventListener("new_alert", (e: any) => {
        try {
          const newAlert: Alert = JSON.parse(e.data);
          console.log("SSE received new alert:", newAlert);
          
          // Mark alert as new to trigger amber pulse animation
          newAlert.isNew = true;
          
          setAlerts((prev) => {
            // Avoid duplicate additions
            if (prev.some((a) => a.id === newAlert.id)) return prev;
            
            // Add to top of list
            const updated = [newAlert, ...prev];
            
            // Remove pulse flag after 3 seconds
            setTimeout(() => {
              setAlerts((curr) =>
                curr.map((a) => (a.id === newAlert.id ? { ...a, isNew: false } : a))
              );
            }, 3000);
            
            return updated;
          });
        } catch (err) {
          console.error("Error parsing new_alert SSE:", err);
        }
      });

      es.addEventListener("alert_updated", (e: any) => {
        try {
          const updateData = JSON.parse(e.data);
          console.log("SSE received alert update:", updateData);
          
          setAlerts((prev) =>
            prev.map((alert) => {
              if (alert.id === updateData.id) {
                return {
                  ...alert,
                  status: updateData.status,
                  event_count: updateData.event_count || alert.event_count,
                  last_seen_at: updateData.last_seen_at || alert.last_seen_at
                };
              }
              return alert;
            })
          );
        } catch (err) {
          console.error("Error parsing alert_updated SSE:", err);
        }
      });

      es.onerror = (err) => {
        console.error("SSE connection error. Retrying in 5s...", err);
        es.close();
        setTimeout(connectSSE, 5000);
      };

      sseRef.current = es;
    };

    connectSSE();

    return () => {
      if (sseRef.current) {
        sseRef.current.close();
      }
    };
  }, []);

  // Client-side search filtering
  const filteredAlerts = alerts.filter((alert) => {
    const q = searchQuery.toLowerCase();
    return (
      (alert.title || "").toLowerCase().includes(q) ||
      (alert.source_ip || "").toLowerCase().includes(q) ||
      (alert.event_type || "").toLowerCase().includes(q)
    );
  });

  // Calculate Metrics from raw queue list
  const metrics = {
    totalOpen: alerts.filter((a) => a.status === "open").length,
    criticalCount: alerts.filter((a) => a.severity === "critical").length,
    highCount: alerts.filter((a) => a.severity === "high").length,
    eventVolume: alerts.reduce((acc, a) => acc + (a.event_count || 1), 0),
  };

  const getSeverityPillColor = (sev: string) => {
    switch (sev) {
      case "all": return severityFilter === "all" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:text-slate-200 border-slate-700";
      case "critical": return severityFilter === "critical" ? "bg-red-650 text-red-200 border-red-800" : "bg-slate-800 text-slate-400 hover:text-red-400 border-slate-700";
      case "high": return severityFilter === "high" ? "bg-orange-650 text-orange-200 border-orange-850" : "bg-slate-800 text-slate-400 hover:text-orange-400 border-slate-700";
      case "medium": return severityFilter === "medium" ? "bg-yellow-650 text-yellow-250 border-yellow-850" : "bg-slate-800 text-slate-400 hover:text-yellow-400 border-slate-700";
      case "low": return severityFilter === "low" ? "bg-green-650 text-green-200 border-green-850" : "bg-slate-800 text-slate-400 hover:text-green-400 border-slate-700";
      default: return "";
    }
  };

  return (
    <Shell>
      <div className="flex flex-col gap-6">
        {/* Title */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-extrabold text-slate-100 uppercase tracking-wider">
              Alerts Queue
            </h1>
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mt-1">
              SOC Threat Triage & ML Analysis Console
            </p>
          </div>
          <button
            onClick={fetchAlerts}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-350 hover:text-slate-100 rounded-lg text-xs font-semibold border border-slate-700/50 transition-colors duration-150"
            title="Refresh alert queue"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Sync
          </button>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Card 1: Total Active */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg flex flex-col justify-between shadow-md">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Alerts</span>
            <span className="text-3xl font-extrabold text-slate-200 mt-2 font-mono">{metrics.totalOpen}</span>
            <span className="text-[9px] text-slate-500 font-bold uppercase mt-1">Triage Pending</span>
          </div>
          {/* Card 2: Critical */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg flex flex-col justify-between shadow-md">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
              <AlertOctagon className="w-3.5 h-3.5 text-critical" />
              Critical Severity
            </span>
            <span className="text-3xl font-extrabold text-critical mt-2 font-mono">{metrics.criticalCount}</span>
            <span className="text-[9px] text-slate-500 font-bold uppercase mt-1">Immediate Action</span>
          </div>
          {/* Card 3: High */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg flex flex-col justify-between shadow-md">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-high" />
              High Severity
            </span>
            <span className="text-3xl font-extrabold text-high mt-2 font-mono">{metrics.highCount}</span>
            <span className="text-[9px] text-slate-500 font-bold uppercase mt-1">Triage this Shift</span>
          </div>
          {/* Card 4: Event Throughput */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg flex flex-col justify-between shadow-md">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              Correlated Logs
            </span>
            <span className="text-3xl font-extrabold text-slate-200 mt-2 font-mono">{metrics.eventVolume}</span>
            <span className="text-[9px] text-slate-500 font-bold uppercase mt-1">Total Normalized logs</span>
          </div>
        </div>

        {/* Filters Panel */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-lg flex flex-col md:flex-row items-center justify-between gap-4 shadow-md">
          {/* Severity Filters */}
          <div className="flex flex-wrap gap-2 w-full md:w-auto">
            {["all", "critical", "high", "medium", "low"].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1.5 rounded text-[11px] font-bold border uppercase tracking-wider transition-all duration-150 ${getSeverityPillColor(sev)}`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Search and Status Dropdown */}
          <div className="flex items-center gap-3 w-full md:w-auto shrink-0">
            {/* Search Input */}
            <div className="relative flex-1 md:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search source IP, name, type..."
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-350 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent transition-all duration-150"
              />
            </div>

            {/* Status Dropdown */}
            <div className="relative">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="appearance-none pl-3 pr-8 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-350 font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent cursor-pointer"
              >
                <option value="all">All States</option>
                <option value="open">Open</option>
                <option value="escalated">Escalated</option>
                <option value="dismissed">Dismissed</option>
                <option value="false_positive">False Positive</option>
                <option value="resolved">Resolved</option>
              </select>
              <Filter className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Alerts Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden shadow-md">
          {loading ? (
            <div className="p-16 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Syncing logs with Postgres...</span>
            </div>
          ) : filteredAlerts.length === 0 ? (
            <div className="p-16 flex flex-col items-center justify-center text-center gap-3">
              <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700/60 flex items-center justify-center">
                <ShieldCheck className="w-6 h-6 text-slate-400" />
              </div>
              <h3 className="text-sm font-bold text-slate-300">All Clear</h3>
              <p className="text-xs text-slate-500 max-w-xs leading-relaxed">
                No active threats matching your filter in the queue.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/60 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    <th className="px-5 py-3.5">Created At</th>
                    <th className="px-5 py-3.5">Severity</th>
                    <th className="px-5 py-3.5">Source IP</th>
                    <th className="px-5 py-3.5">Triage Alert Details</th>
                    <th className="px-5 py-3.5">MITRE ATT&CK Tactic</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5 text-center">Events</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {filteredAlerts.map((alert) => (
                    <tr
                      key={alert.id}
                      onClick={() => router.push(`/alerts/${alert.id}`)}
                      className={`
                        group border-b border-slate-800 hover:bg-slate-800/40
                        cursor-pointer transition-all duration-150
                        ${alert.isNew ? "animate-new-row" : ""}
                      `}
                    >
                      <td className="px-5 py-3.5 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                        {new Date(alert.created_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-3.5">
                        <SeverityBadge severity={alert.severity} />
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs font-semibold text-slate-200">
                        {alert.source_ip || "Internal"}
                      </td>
                      <td className="px-5 py-3.5 max-w-xs md:max-w-sm truncate text-xs font-medium text-slate-300 group-hover:text-slate-100">
                        {alert.title}
                      </td>
                      <td className="px-5 py-3.5">
                        <MitreBadge tacticName={alert.mitre_tactic} techniqueId={alert.mitre_technique_id} />
                      </td>
                      <td className="px-5 py-3.5">
                        <StatusBadge status={alert.status} />
                      </td>
                      <td className="px-5 py-3.5 text-center font-mono text-xs font-bold text-slate-400">
                        {alert.event_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}
