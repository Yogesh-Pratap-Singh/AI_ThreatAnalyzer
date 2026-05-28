import React from "react";
import { Shield, ShieldAlert, ShieldCheck, ShieldX, Clock } from "lucide-react";

type StatusType = "open" | "escalated" | "dismissed" | "false_positive" | "resolved";

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const stat = (status || "open").toLowerCase() as StatusType;

  const config = {
    open: {
      label: "Open",
      icon: Clock,
      classes: "bg-amber-950/50 text-amber-300 border-amber-800/50",
    },
    escalated: {
      label: "Escalated",
      icon: ShieldAlert,
      classes: "bg-red-950/50 text-red-300 border-red-800/50 animate-pulse",
    },
    dismissed: {
      label: "Dismissed",
      icon: ShieldX,
      classes: "bg-slate-900/80 text-slate-400 border-slate-700/50",
    },
    false_positive: {
      label: "False Positive",
      icon: ShieldCheck,
      classes: "bg-green-950/50 text-green-300 border-green-800/50",
    },
    resolved: {
      label: "Resolved",
      icon: Shield,
      classes: "bg-blue-950/50 text-blue-300 border-blue-800/50",
    },
  };

  const selected = config[stat] || config.open;
  const Icon = selected.icon;

  return (
    <span
      className={`
        inline-flex items-center gap-1 px-2 py-0.5
        rounded text-[11px] font-semibold tracking-wide
        border transition-colors duration-150
        ${selected.classes}
      `}
      role="status"
      aria-label={`Status: ${selected.label}`}
    >
      <Icon className="w-3 h-3" aria-hidden="true" />
      {selected.label}
    </span>
  );
}
