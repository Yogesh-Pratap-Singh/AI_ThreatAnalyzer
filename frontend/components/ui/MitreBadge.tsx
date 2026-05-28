import React from "react";
import { ExternalLink } from "lucide-react";

interface MitreBadgeProps {
  tacticName: string | null;
  techniqueId: string | null;
}

export default function MitreBadge({ tacticName, techniqueId }: MitreBadgeProps) {
  if (!tacticName && !techniqueId) {
    return <span className="text-xs text-slate-500">—</span>;
  }

  // Parse root technique ID (e.g. T1048.003 -> T1048) for linking
  const rootId = techniqueId ? techniqueId.split(".")[0] : "";
  const mitreUrl = rootId ? `https://attack.mitre.org/techniques/${rootId}` : null;

  const content = (
    <>
      {tacticName || "Tactic"}
      {techniqueId && (
        <span className="opacity-80 font-mono text-[10px] ml-1 px-1 py-0.2 bg-slate-900/50 rounded border border-slate-700">
          {techniqueId}
        </span>
      )}
    </>
  );

  const classes = `
    inline-flex items-center gap-1.5
    px-2 py-0.5
    rounded text-[11px] font-medium
    bg-blue-950/80 text-blue-300 border border-blue-900/50
    hover:bg-blue-900/50 hover:text-blue-200 transition-colors duration-150
  `;

  if (mitreUrl) {
    return (
      <a
        href={mitreUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={classes}
        title="View MITRE ATT&CK technique details"
      >
        <ExternalLink className="w-3 h-3 text-blue-400" aria-hidden="true" />
        {content}
      </a>
    );
  }

  return (
    <span className={classes}>
      {content}
    </span>
  );
}
