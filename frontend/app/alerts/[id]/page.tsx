"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ChevronLeft, ShieldAlert, Send, Clock, User, AlertOctagon, CornerDownRight, Check, X, Loader2 } from "lucide-react";
import Shell from "@/components/layout/Shell";
import SeverityBadge from "@/components/ui/SeverityBadge";
import StatusBadge from "@/components/ui/StatusBadge";
import MitreBadge from "@/components/ui/MitreBadge";
import AIExplanationCard from "@/components/ui/AIExplanationCard";
import JsonViewer from "@/components/ui/JsonViewer";
import api from "@/lib/api";

interface Note {
  id: string;
  user?: { id: string; full_name: string };
  content: string;
  created_at: string;
}

interface RelatedEvent {
  id: string;
  event_time: string;
  event_type: string;
  bytes_transferred: number | null;
  anomaly_score: number;
}

interface AlertDetail {
  id: string;
  title: string;
  severity: string;
  severity_score: number;
  severity_breakdown: {
    anomaly_score: number;
    intel_match_score: number;
    tactic_weight: number;
    asset_criticality: number;
  };
  source_ip: string | null;
  dest_ip: string | null;
  source_port: number | null;
  dest_port: number | null;
  event_type: string;
  bytes_transferred: number | null;
  mitre_tactic: string | null;
  mitre_technique_id: string | null;
  mitre_technique_name: string | null;
  mitre_confidence: number | null;
  mitre_url: string | null;
  status: string;
  event_count: number;
  first_seen_at: string;
  last_seen_at: string;
  created_at: string;
  notes: Note[];
}

export default function AlertDetailPage() {
  const { id } = useParams();
  const router = useRouter();

  const [alert, setAlert] = useState<AlertDetail | null>(null);
  const [relatedEvents, setRelatedEvents] = useState<RelatedEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Notes state
  const [newNote, setNewNote] = useState("");
  const [noteSubmitting, setNoteSubmitting] = useState(false);

  // Modals state
  const [showEscalate, setShowEscalate] = useState(false);
  const [escalatePriority, setEscalatePriority] = useState("P1");
  const [escalateNote, setEscalateNote] = useState("");
  const [escalateSubmitting, setEscalateSubmitting] = useState(false);

  const [showFalsePos, setShowFalsePos] = useState(false);
  const [fpReason, setFpReason] = useState("scheduled_job");
  const [fpNote, setFpNote] = useState("");
  const [fpSubmitting, setFpSubmitting] = useState(false);

  const [actionError, setActionError] = useState<string | null>(null);

  const fetchAlertDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/alerts/${id}`);
      setAlert(response.data.alert);
      setRelatedEvents(response.data.related_events || []);
    } catch (err: any) {
      console.error("Failed to load alert details:", err);
      setError(err.response?.data?.detail?.message || "Failed to load alert information.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchAlertDetails();
    }
  }, [id]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;

    setNoteSubmitting(true);
    try {
      const response = await api.post(`/alerts/${id}/notes`, { content: newNote });
      // Add note locally to thread list
      if (alert) {
        setAlert({
          ...alert,
          notes: [...alert.notes, response.data]
        });
      }
      setNewNote("");
    } catch (err) {
      console.error("Failed to add note:", err);
    } finally {
      setNoteSubmitting(false);
    }
  };

  const handleTriageAction = async (action: string, payload: any) => {
    setActionError(null);
    try {
      const response = await api.patch(`/alerts/${id}/action`, payload);
      // Reload details to sync L2 state
      fetchAlertDetails();
      setShowEscalate(false);
      setShowFalsePos(false);
    } catch (err: any) {
      console.error("Failed to perform triage action:", err);
      const msg = err.response?.data?.detail?.message || "Action failed. Alert might be lock-actioned.";
      setActionError(msg);
    }
  };

  const executeEscalate = async () => {
    setEscalateSubmitting(true);
    // Assign to a dummy analyst UUID for local mock (admin or self)
    const dummyAssignee = "3fa85f64-5717-4562-b3fc-2c963f66afa6";
    await handleTriageAction("escalate", {
      action: "escalate",
      priority: escalatePriority,
      assignee_id: dummyAssignee,
      note: escalateNote
    });
    setEscalateSubmitting(false);
  };

  const executeFalsePositive = async () => {
    setFpSubmitting(true);
    await handleTriageAction("false_positive", {
      action: "false_positive",
      priority: fpReason, // map to feedback schemas
      note: fpNote
    });
    setFpSubmitting(false);
  };

  const executeDismiss = async () => {
    if (confirm("Are you sure you want to dismiss this alert?")) {
      await handleTriageAction("dismiss", {
        action: "dismiss",
        note: "Alert dismissed directly from details dashboard."
      });
    }
  };

  const isActioned = alert && alert.status !== "open";

  return (
    <Shell>
      <div className="flex flex-col gap-6">
        {/* Back navigation */}
        <button
          onClick={() => router.push("/dashboard")}
          className="flex items-center gap-1.5 text-slate-450 hover:text-slate-200 text-xs font-semibold self-start transition-colors duration-150"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Queue
        </button>

        {loading && (
          <div className="p-20 text-center flex flex-col items-center justify-center gap-2">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Loading investigation metrics...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-950/40 border border-red-900/50 p-6 rounded-lg text-center max-w-lg mx-auto">
            <h3 className="font-bold text-red-400">Error Loading Alert</h3>
            <p className="text-xs text-red-300 mt-2">{error}</p>
            <button
              onClick={() => router.push("/dashboard")}
              className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-750 text-xs text-slate-200 border border-slate-700/60 rounded font-semibold transition-all duration-150"
            >
              Return to Console
            </button>
          </div>
        )}

        {alert && !loading && !error && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Left Section (65%) */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              {/* Alert Header card */}
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 shadow-md flex flex-col gap-3">
                <div className="flex flex-wrap items-center gap-3">
                  <SeverityBadge severity={alert.severity} />
                  <StatusBadge status={alert.status} />
                  <span className="text-[10px] font-bold text-slate-500 font-mono">
                    ID: {alert.id}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-slate-100 mt-1 leading-snug">
                  {alert.title}
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 pt-4 border-t border-slate-850/60 text-xs text-slate-400">
                  <div className="flex flex-col">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 mb-0.5">Source IP</span>
                    <span className="font-mono text-slate-200 font-semibold">{alert.source_ip || "Internal"}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 mb-0.5">Destination IP</span>
                    <span className="font-mono text-slate-200 font-semibold">{alert.dest_ip || "—"}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 mb-0.5">Event Category</span>
                    <span className="text-slate-200 font-semibold uppercase text-[11px] tracking-wider">{alert.event_type.replace("_", " ")}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-slate-500 mb-0.5">MITRE Technique</span>
                    <span className="text-slate-200 font-semibold">
                      {alert.mitre_technique_id ? (
                        <MitreBadge tacticName={alert.mitre_tactic} techniqueId={alert.mitre_technique_id} />
                      ) : (
                        "None detected"
                      )}
                    </span>
                  </div>
                </div>
              </div>

              {/* AI RAG summary card */}
              <AIExplanationCard alertId={alert.id} />

              {/* Related Events Timeline */}
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 shadow-md flex flex-col gap-4">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-850/60">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <h3 className="text-xs font-bold text-slate-250 uppercase tracking-wider">
                    Alert Events Timeline (Last 24 Hours)
                  </h3>
                </div>
                {relatedEvents.length === 0 ? (
                  <p className="text-xs text-slate-550 italic text-center py-4">No associated raw events recorded.</p>
                ) : (
                  <div className="overflow-x-auto max-h-[220px]">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="text-[9px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800">
                          <th className="py-2.5">Time</th>
                          <th className="py-2.5">Event Type</th>
                          <th className="py-2.5">Bytes</th>
                          <th className="py-2.5 text-right">Anomaly Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-850/40">
                        {relatedEvents.map((ev) => (
                          <tr key={ev.id} className="text-slate-350 hover:text-slate-200 font-medium">
                            <td className="py-2 font-mono text-[10.5px] text-slate-400">{new Date(ev.event_time).toLocaleString()}</td>
                            <td className="py-2 uppercase text-[10px] tracking-wider font-semibold text-slate-400">{ev.event_type.replace("_", " ")}</td>
                            <td className="py-2 font-mono text-[11px]">{ev.bytes_transferred !== null ? `${(ev.bytes_transferred / (1024 * 1024)).toFixed(2)} MB` : "—"}</td>
                            <td className="py-2 text-right font-mono font-bold text-amber-400">{ev.anomaly_score.toFixed(4)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Raw JSON payload viewer */}
              {relatedEvents.length > 0 && (
                <JsonViewer data={relatedEvents[0]} title={`Raw Event Sample (${relatedEvents[0].id})`} />
              )}
            </div>

            {/* Right Section (35%) */}
            <div className="flex flex-col gap-6">
              {/* Triage Actions panel */}
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-md flex flex-col gap-4">
                <h3 className="text-xs font-bold text-slate-250 uppercase tracking-wider pb-2 border-b border-slate-850/60">
                  Triage Investigation Actions
                </h3>
                {actionError && (
                  <div className="text-[11px] text-red-300 bg-red-950/40 border border-red-900/40 p-2 rounded">
                    {actionError}
                  </div>
                )}

                {isActioned ? (
                  <div className="flex items-start gap-2.5 p-3.5 bg-slate-950/40 border border-slate-800 rounded-lg text-xs text-slate-400 font-medium leading-relaxed">
                    <ShieldAlert className="w-4 h-4 mt-0.5 text-slate-500 flex-shrink-0" />
                    <div>
                      <span>This alert has already been resolved and locked. Action was recorded as: </span>
                      <span className="font-bold text-slate-300 uppercase block mt-1">{alert.status.replace("_", " ")}</span>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2.5">
                    {/* Action buttons */}
                    <button
                      onClick={() => setShowEscalate(true)}
                      className="w-full flex items-center justify-center gap-1.5 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-bold uppercase tracking-wider transition-colors duration-150 active:scale-97 shadow-md"
                    >
                      <ShieldAlert className="w-4 h-4" />
                      Escalate Alert
                    </button>
                    <button
                      onClick={() => setShowFalsePos(true)}
                      className="w-full py-2 bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700/50 rounded text-xs font-bold uppercase tracking-wider transition-colors duration-150 active:scale-97"
                    >
                      False Positive
                    </button>
                    <button
                      onClick={executeDismiss}
                      className="w-full py-2 bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700/50 rounded text-xs font-bold uppercase tracking-wider transition-colors duration-150 active:scale-97"
                    >
                      Dismiss Alert
                    </button>
                  </div>
                )}

                {/* Score breakdown metrics */}
                <div className="mt-4 pt-4 border-t border-slate-850/60 flex flex-col gap-3 text-xs">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Severity Score Breakdown</span>
                  <div className="flex flex-col gap-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">ML Anomaly Weight (40%)</span>
                      <span className="font-mono text-slate-200 font-bold">{(alert.severity_breakdown.anomaly_score * 0.4).toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Intel Match Weight (30%)</span>
                      <span className="font-mono text-slate-200 font-bold">{(alert.severity_breakdown.intel_match_score * 0.3).toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">MITRE Tactic Weight (20%)</span>
                      <span className="font-mono text-slate-200 font-bold">{(alert.severity_breakdown.tactic_weight * 0.2).toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Asset Importance (10%)</span>
                      <span className="font-mono text-slate-200 font-bold">{(alert.severity_breakdown.asset_criticality * 0.1).toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t border-slate-850/60 font-bold">
                      <span className="text-slate-300">Composite Risk Score</span>
                      <span className="font-mono text-blue-400">{(alert.severity_score).toFixed(4)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Notes thread & submit */}
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-md flex flex-col gap-4">
                <h3 className="text-xs font-bold text-slate-250 uppercase tracking-wider pb-2 border-b border-slate-850/60">
                  Analyst Collaboration Notes
                </h3>

                {/* List of Notes */}
                <div className="flex flex-col gap-3 max-h-[220px] overflow-auto pr-1">
                  {alert.notes.length === 0 ? (
                    <p className="text-xs text-slate-550 italic py-2 text-center">No analyst notes recorded yet.</p>
                  ) : (
                    alert.notes.map((note) => (
                      <div key={note.id} className="bg-slate-950/40 border border-slate-850 rounded p-2.5 flex flex-col gap-1.5">
                        <div className="flex items-center justify-between text-[10px] text-slate-500 font-semibold font-mono">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3 text-slate-400" />
                            {note.user?.full_name || "System"}
                          </span>
                          <span>{new Date(note.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-xs text-slate-350 leading-relaxed font-sans">{note.content}</p>
                      </div>
                    ))
                  )}
                </div>

                {/* Add note form */}
                <form onSubmit={handleAddNote} className="flex gap-2 mt-2 pt-4 border-t border-slate-850/60">
                  <input
                    type="text"
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    placeholder="Add notes, context, status..."
                    className="flex-1 px-3 py-2 bg-slate-950 border border-slate-800 rounded text-xs text-slate-350 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent transition-all duration-150"
                  />
                  <button
                    type="submit"
                    disabled={noteSubmitting || !newNote.trim()}
                    className="p-2 bg-blue-600 hover:bg-blue-500 text-white rounded transition-all duration-150 disabled:opacity-40 active:scale-95 flex items-center justify-center"
                    aria-label="Send note"
                  >
                    {noteSubmitting ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Send className="w-3.5 h-3.5" />
                    )}
                  </button>
                </form>
              </div>
            </div>

          </div>
        )}

        {/* Modal: Escalate */}
        {showEscalate && (
          <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
            <div className="relative bg-slate-900 border border-slate-800 rounded-lg shadow-xl p-6 w-full max-w-md animate-slide-up">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-red-500" />
                  Escalate Incident Queue
                </h2>
                <button onClick={() => setShowEscalate(false)} className="text-slate-500 hover:text-slate-350">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="mt-4 flex flex-col gap-4">
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Escalation SLA Priority
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {["P1", "P2", "P3"].map((p) => (
                      <button
                        key={p}
                        onClick={() => setEscalatePriority(p)}
                        className={`py-2 rounded text-xs font-bold border transition-all duration-150 ${
                          escalatePriority === p
                            ? "bg-red-600 text-white border-red-500"
                            : "bg-slate-950 text-slate-450 border-slate-850 hover:text-slate-300"
                        }`}
                      >
                        {p} (SLA)
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="escalate-note" className="block text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Escalation Notes / Investigation Context
                  </label>
                  <textarea
                    id="escalate-note"
                    value={escalateNote}
                    onChange={(e) => setEscalateNote(e.target.value)}
                    placeholder="e.g. host isolated, Tor connections verified from finance user."
                    className="w-full px-3 py-2.5 h-24 bg-slate-950 border border-slate-850 rounded text-xs text-slate-350 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent transition-all duration-150 resize-none"
                  />
                </div>
              </div>
              <div className="flex gap-3 justify-end mt-6 pt-4 border-t border-slate-800">
                <button
                  onClick={() => setShowEscalate(false)}
                  className="px-4 py-2 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-bold uppercase rounded tracking-wider transition-colors duration-150"
                >
                  Cancel
                </button>
                <button
                  onClick={executeEscalate}
                  disabled={escalateSubmitting || !escalateNote.trim()}
                  className="px-4 py-2 bg-red-650 hover:bg-red-500 text-white text-xs font-bold uppercase rounded tracking-wider transition-colors duration-150 disabled:opacity-40 active:scale-97"
                >
                  {escalateSubmitting ? "Escalating..." : "Confirm Escalation"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: False Positive */}
        {showFalsePos && (
          <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
            <div className="relative bg-slate-900 border border-slate-800 rounded-lg shadow-xl p-6 w-full max-w-md animate-slide-up">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                  <CornerDownRight className="w-4 h-4 text-green-500" />
                  Mark as False Positive
                </h2>
                <button onClick={() => setShowFalsePos(false)} className="text-slate-500 hover:text-slate-350">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="mt-4 flex flex-col gap-4">
                <div className="space-y-1.5">
                  <label htmlFor="fp-reason" className="block text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Reason Category
                  </label>
                  <select
                    id="fp-reason"
                    value={fpReason}
                    onChange={(e) => setFpReason(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-850 rounded text-xs text-slate-350 focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
                  >
                    <option value="scheduled_job">Scheduled backup / IT job</option>
                    <option value="known_safe">Known safe domain / user traffic</option>
                    <option value="misconfiguration">Asset network misconfiguration</option>
                    <option value="other">Other reason</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label htmlFor="fp-note" className="block text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    Feedback Details (Helps Retrain ML Model)
                  </label>
                  <textarea
                    id="fp-note"
                    value={fpNote}
                    onChange={(e) => setFpNote(e.target.value)}
                    placeholder="e.g. backup server transferring weekly DB dump to local server."
                    className="w-full px-3 py-2.5 h-24 bg-slate-950 border border-slate-850 rounded text-xs text-slate-350 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent transition-all duration-150 resize-none"
                  />
                </div>
              </div>
              <div className="flex gap-3 justify-end mt-6 pt-4 border-t border-slate-800">
                <button
                  onClick={() => setShowFalsePos(false)}
                  className="px-4 py-2 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-bold uppercase rounded tracking-wider transition-colors duration-150"
                >
                  Cancel
                </button>
                <button
                  onClick={executeFalsePositive}
                  disabled={fpSubmitting || !fpNote.trim()}
                  className="px-4 py-2 bg-green-650 hover:bg-green-600 text-white text-xs font-bold uppercase rounded tracking-wider transition-colors duration-150 disabled:opacity-40 active:scale-97"
                >
                  {fpSubmitting ? "Submitting..." : "Confirm Classification"}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </Shell>
  );
}
