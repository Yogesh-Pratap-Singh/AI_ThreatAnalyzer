"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";
import { Sparkles, ThumbsUp, ThumbsDown, Loader2, RefreshCw, CheckCircle2 } from "lucide-react";

interface AIExplanationCardProps {
  alertId: string;
}

export default function AIExplanationCard({ alertId }: AIExplanationCardProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<{
    explanation: string | null;
    mitre_tactic: string | null;
    mitre_technique_id: string | null;
    recommended_action: string | null;
    model_used: string;
  } | null>(null);

  const [feedbackSent, setFeedbackSent] = useState<"helpful" | "not_helpful" | null>(null);

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `http://localhost:8000/api/v1/alerts/${alertId}/explanation`,
        { withCredentials: true }
      );
      setData(response.data);
    } catch (err: any) {
      console.error("Failed to load explanation:", err);
      setError("AI analysis engine currently unreachable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExplanation();
  }, [alertId]);

  const handleFeedback = async (type: "helpful" | "not_helpful") => {
    if (feedbackSent) return;
    try {
      await axios.post(
        "http://localhost:8000/api/v1/feedback",
        {
          alert_id: alertId,
          feedback_type: type === "helpful" ? "explanation_helpful" : "explanation_not_helpful",
        },
        { withCredentials: true }
      );
      setFeedbackSent(type);
    } catch (err) {
      console.error("Failed to send feedback", err);
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700/60 rounded-lg p-5 shadow-md flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center gap-2 pb-3 border-b border-slate-700/50">
        <Sparkles className="w-5 h-5 text-blue-400 animate-pulse" />
        <h3 className="text-[13px] font-bold text-slate-200 uppercase tracking-wider">
          AI-Powered Threat Analysis
        </h3>
        {data && (
          <span className="ml-auto text-[10px] text-slate-500 font-medium font-mono uppercase">
            Powered by {data.model_used.split("/").pop()}
          </span>
        )}
      </div>

      {/* Content States */}
      {loading && (
        <div className="space-y-3 py-2">
          {/* Shimmer loading skeleton */}
          <div className="h-4 bg-slate-700/50 rounded w-full animate-pulse" />
          <div className="h-4 bg-slate-700/50 rounded w-[92%] animate-pulse" />
          <div className="h-4 bg-slate-700/50 rounded w-[85%] animate-pulse" />
          <div className="h-4 bg-slate-700/50 rounded w-[40%] animate-pulse mt-4" />
        </div>
      )}

      {error && (
        <div className="flex flex-col items-start gap-2 py-4">
          <p className="text-sm text-slate-400 italic">{error}</p>
          <button
            onClick={fetchExplanation}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-650 text-slate-200 rounded text-xs font-semibold transition-all duration-150 active:scale-95 border border-slate-600/40"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry Generation
          </button>
        </div>
      )}

      {data && !loading && !error && (
        <div className="flex flex-col gap-4">
          {/* Explanation Text */}
          <p className="text-sm text-slate-200 leading-relaxed font-sans">
            {data.explanation || "No explanation returned by the model."}
          </p>

          {/* Recommended Action */}
          {data.recommended_action && (
            <div className="bg-blue-950/20 border border-blue-900/30 rounded p-3 mt-1 flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">
                Recommended Actions
              </span>
              <p className="text-xs text-blue-200 font-medium leading-relaxed">
                {data.recommended_action}
              </p>
            </div>
          )}

          {/* Feedback controls */}
          <div className="flex items-center gap-3 pt-3 border-t border-slate-700/50 text-xs">
            {feedbackSent ? (
              <div className="flex items-center gap-1 text-green-400 font-semibold text-[11px]">
                <CheckCircle2 className="w-4 h-4" />
                Thanks for your feedback!
              </div>
            ) : (
              <>
                <span className="text-slate-400 text-[11px]">Was this summary helpful?</span>
                <button
                  onClick={() => handleFeedback("helpful")}
                  className="flex items-center gap-1 text-slate-400 hover:text-green-400 hover:scale-105 transition-all duration-150 px-1 py-0.5"
                  aria-label="Explanation is helpful"
                >
                  <ThumbsUp className="w-3.5 h-3.5" />
                  Yes
                </button>
                <button
                  onClick={() => handleFeedback("not_helpful")}
                  className="flex items-center gap-1 text-slate-400 hover:text-red-400 hover:scale-105 transition-all duration-150 px-1 py-0.5"
                  aria-label="Explanation is not helpful"
                >
                  <ThumbsDown className="w-3.5 h-3.5" />
                  No
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
