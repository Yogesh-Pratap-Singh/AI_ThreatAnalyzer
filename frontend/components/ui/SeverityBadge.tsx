import React from "react";
import { AlertOctagon, AlertTriangle, AlertCircle, Info } from "lucide-react";

type SeverityType = "critical" | "high" | "medium" | "low";

interface SeverityBadgeProps {
  severity: string;
}

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const sev = (severity || "low").toLowerCase() as SeverityType;

  const config = {
    critical: {
      label: "Critical",
      icon: AlertOctagon,
      classes: "bg-critical-bg text-critical border-critical/50 hover:bg-critical-bg/85",
    },
    high: {
      label: "High",
      icon: AlertTriangle,
      classes: "bg-high-bg text-high border-high/50 hover:bg-high-bg/85",
    },
    medium: {
      label: "Medium",
      icon: AlertCircle,
      classes: "bg-medium-bg text-medium border-medium/50 hover:bg-medium-bg/85",
    },
    low: {
      label: "Low",
      icon: Info,
      classes: "bg-low-bg text-low border-low/50 hover:bg-low-bg/85",
    },
  };

  const selected = config[sev] || config.low;
  const Icon = selected.icon;

  return (
    <span
      className={`
        inline-flex items-center gap-1.5
        px-2.5 py-0.5
        rounded text-xs font-semibold uppercase tracking-wider
        border transition-colors duration-150
        ${selected.classes}
      `}
      role="status"
      aria-label={`Severity: ${selected.label}`}
    >
      <Icon className="w-3.5 h-3.5" aria-hidden="true" />
      {selected.label}
    </span>
  );
}
