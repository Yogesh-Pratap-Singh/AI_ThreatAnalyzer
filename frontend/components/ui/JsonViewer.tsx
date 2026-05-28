"use client";

import React, { useState } from "react";
import { Copy, Check } from "lucide-react";

interface JsonViewerProps {
  data: any;
  title?: string;
}

export default function JsonViewer({ data, title = "Raw Payload" }: JsonViewerProps) {
  const [copied, setCopied] = useState(false);

  const formattedJson = JSON.stringify(data, null, 2);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(formattedJson);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy JSON:", err);
    }
  };

  // Helper to colorize JSON tokens
  const syntaxHighlight = (jsonStr: string) => {
    // Escape HTML
    let escaped = jsonStr
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Match JSON keys, strings, numbers, booleans, and nulls
    const regex = /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g;
    
    return escaped.replace(regex, (match) => {
      let cls = "text-amber-400"; // default number/literal
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = "text-blue-300 font-semibold"; // key
        } else {
          cls = "text-emerald-400"; // string value
        }
      } else if (/true|false/.test(match)) {
        cls = "text-purple-400 font-medium"; // boolean
      } else if (/null/.test(match)) {
        cls = "text-slate-500 italic"; // null
      }
      return `<span class="${cls}">${match}</span>`;
    });
  };

  const highlightedHtml = syntaxHighlight(formattedJson);

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex flex-col max-h-[350px]">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-900 bg-slate-900/50">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-slate-200 transition-colors duration-150 py-0.5 px-2 bg-slate-800 hover:bg-slate-750 rounded border border-slate-700/40"
          aria-label="Copy JSON code to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-green-400" />
              Copied!
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              Copy
            </>
          )}
        </button>
      </div>

      {/* Code Area */}
      <div className="p-4 overflow-auto font-mono text-[11px] leading-relaxed text-slate-300">
        <pre 
          className="whitespace-pre-wrap break-all"
          dangerouslySetInnerHTML={{ __html: highlightedHtml }}
        />
      </div>
    </div>
  );
}
