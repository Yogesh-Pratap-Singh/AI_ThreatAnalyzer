# Frontend Design System & Guidelines
# AI Threat Analyzer

**Version**: 1.0  
**Last Updated**: 2026-05-27  

---

## 1. Design Principles

1. **Clarity under pressure**: SOC analysts read this dashboard at 3 AM. Every element must be instantly scannable. No decoration that competes with critical information.
2. **Severity is sacred**: Color is not decorative — red always means critical threat. Never use red for anything else.
3. **Density with breathing room**: Security dashboards pack a lot of information. Use compact layouts but preserve enough whitespace that eyes don't fatigue.
4. **Progressive disclosure**: Show the most important signal first (severity, what happened). Details are one click away, not all on screen at once.
5. **Accessibility always**: Analysts may have color vision deficiencies. Severity must be communicated via icon + label + color, never color alone.

---

## 2. Design Tokens

### Color Palette

#### Severity Colors (NEVER use for non-severity purposes)

```css
/* Critical — immediate action required */
--color-critical: #ef4444;
--color-critical-bg: #fef2f2;
--color-critical-border: #fca5a5;
--color-critical-text: #991b1b;

/* High — action required this shift */
--color-high: #f97316;
--color-high-bg: #fff7ed;
--color-high-border: #fdba74;
--color-high-text: #9a3412;

/* Medium — review today */
--color-medium: #eab308;
--color-medium-bg: #fefce8;
--color-medium-border: #fde047;
--color-medium-text: #854d0e;

/* Low — informational */
--color-low: #22c55e;
--color-low-bg: #f0fdf4;
--color-low-border: #86efac;
--color-low-text: #166534;
```

#### Brand / Primary Colors

```css
--color-primary-50: #eff6ff;
--color-primary-100: #dbeafe;
--color-primary-200: #bfdbfe;
--color-primary-300: #93c5fd;
--color-primary-400: #60a5fa;
--color-primary-500: #3b82f6;   /* Main brand */
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;
--color-primary-800: #1e40af;
--color-primary-900: #1e3a8a;
```

#### Neutral Colors

```css
--color-neutral-50: #f9fafb;
--color-neutral-100: #f3f4f6;
--color-neutral-200: #e5e7eb;
--color-neutral-300: #d1d5db;
--color-neutral-400: #9ca3af;
--color-neutral-500: #6b7280;
--color-neutral-600: #4b5563;
--color-neutral-700: #374151;
--color-neutral-800: #1f2937;
--color-neutral-900: #111827;
```

#### Semantic Colors (non-severity)

```css
--color-success: #10b981;
--color-info: #3b82f6;
--color-warning: #f59e0b;    /* Use ONLY for system/UI warnings, NOT threat severity */
--color-error: #ef4444;       /* Use ONLY for form errors and system errors */
```

#### Dark Mode (Default for Dashboard)

The dashboard defaults to dark mode — analysts work in low-light NOC environments.

```css
/* Dark mode overrides */
--bg-primary: #0f172a;         /* Page background */
--bg-secondary: #1e293b;       /* Card / panel background */
--bg-tertiary: #334155;        /* Hover states, table stripes */
--text-primary: #f1f5f9;
--text-secondary: #94a3b8;
--text-tertiary: #64748b;
--border-color: #334155;
```

---

### Typography

#### Font Families

```css
--font-sans: 'Inter', 'Segoe UI', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
```

Font mono is used for: IP addresses, event IDs, raw JSON, timestamps, score values.

#### Font Sizes

```css
--text-xs: 0.75rem;    /* 12px — timestamps, badges, metadata */
--text-sm: 0.875rem;   /* 14px — table cells, secondary text */
--text-base: 1rem;     /* 16px — body, descriptions */
--text-lg: 1.125rem;   /* 18px — card titles */
--text-xl: 1.25rem;    /* 20px — section headings */
--text-2xl: 1.5rem;    /* 24px — page headings */
--text-3xl: 1.875rem;  /* 30px — KPI numbers */
```

#### Font Weights

```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

#### Usage Guidelines

- KPI numbers (alert counts): `font-bold text-3xl`
- Page headings: `font-semibold text-2xl`
- Card titles: `font-semibold text-lg`
- Table headers: `font-medium text-sm uppercase tracking-wide`
- Table cells: `font-normal text-sm`
- IP addresses / hashes: `font-mono text-sm`
- AI explanation body text: `font-normal text-base leading-relaxed`
- Timestamps: `font-mono text-xs text-secondary`

---

### Spacing Scale

```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

Usage rules:

- Table cell padding: `px-4 py-3` (16px × 12px)
- Card padding: `p-6` (24px)
- Section spacing: `mb-8` to `mb-12`
- Badge padding: `px-2 py-0.5`
- Modal padding: `p-6`

---

### Border Radius

```css
--radius-sm: 0.25rem;   /* 4px — badges, tags */
--radius-md: 0.375rem;  /* 6px — inputs, small cards */
--radius-lg: 0.5rem;    /* 8px — cards, panels */
--radius-xl: 0.75rem;   /* 12px — modals */
--radius-full: 9999px;  /* pills, avatars */
```

---

### Shadows (Dark mode)

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.4);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.6);
```

---

## 3. Layout System

### Application Shell

```
┌─────────────────────────────────────────────────┐
│  Sidebar (240px fixed)  │  Main Content Area    │
│  ─────────────────────  │  ─────────────────    │
│  Logo                   │  Top bar (56px)       │
│  Nav items              │  ─────────────────    │
│  ─────────────────────  │  Page content         │
│  Status indicators      │  (scrollable)         │
└─────────────────────────────────────────────────┘
```

### Grid System

- **Container**: `max-w-7xl mx-auto px-6`
- **Dashboard grid**: 12-column, `gap-6`
- **KPI cards row**: 4 equal columns (`grid-cols-4`)
- **Alert table**: Full width

### Responsive Breakpoints

```css
sm: 640px    /* tablet portrait */
md: 768px    /* tablet landscape */
lg: 1024px   /* desktop */
xl: 1280px   /* wide desktop — primary target */
2xl: 1536px  /* ultra-wide */
```

---

## 4. Component Library

---

### Severity Badge

The most important component. Used on every alert row and detail view.

```tsx
// Variants: "critical" | "high" | "medium" | "low"
const severityConfig = {
  critical: {
    label: "Critical",
    icon: "🔴",  // replaced with Lucide AlertOctagon
    classes: "bg-red-950 text-red-300 border border-red-800",
  },
  high: {
    label: "High",
    icon: "🟠",  // replaced with Lucide AlertTriangle
    classes: "bg-orange-950 text-orange-300 border border-orange-800",
  },
  medium: {
    label: "Medium",
    icon: "🟡",  // replaced with Lucide AlertCircle
    classes: "bg-yellow-950 text-yellow-300 border border-yellow-800",
  },
  low: {
    label: "Low",
    icon: "🟢",  // replaced with Lucide Info
    classes: "bg-green-950 text-green-300 border border-green-800",
  },
};

<span
  className={`
    inline-flex items-center gap-1.5
    px-2 py-0.5
    rounded text-xs font-medium
    ${severityConfig[severity].classes}
  `}
  role="status"
  aria-label={`Severity: ${severityConfig[severity].label}`}
>
  <SeverityIcon className="w-3 h-3" aria-hidden="true" />
  {severityConfig[severity].label}
</span>
```

**Rule**: Severity badge is ALWAYS icon + label. Never icon-only (accessibility). Never color-only.

---

### MITRE ATT&CK Tactic Badge

```tsx
<a
  href={`https://attack.mitre.org/techniques/${techniqueId}`}
  target="_blank"
  rel="noopener noreferrer"
  className="
    inline-flex items-center gap-1.5
    px-2 py-0.5
    rounded text-xs font-medium
    bg-blue-950 text-blue-300 border border-blue-800
    hover:bg-blue-900 transition-colors duration-150
  "
>
  <ExternalLink className="w-3 h-3" aria-hidden="true" />
  {tacticName} · {techniqueId}
</a>
```

---

### Alert Table Row

```tsx
<tr
  className="
    border-b border-slate-800
    hover:bg-slate-800/50
    cursor-pointer
    transition-colors duration-100
  "
  onClick={() => router.push(`/alerts/${alert.id}`)}
>
  <td className="px-4 py-3 font-mono text-xs text-slate-400">
    {formatTimestamp(alert.created_at)}
  </td>
  <td className="px-4 py-3">
    <SeverityBadge severity={alert.severity} />
  </td>
  <td className="px-4 py-3 font-mono text-sm text-slate-200">
    {alert.source_ip}
  </td>
  <td className="px-4 py-3 text-sm text-slate-300 max-w-xs truncate">
    {alert.event_type}
  </td>
  <td className="px-4 py-3">
    <MitreBadge tacticName={alert.mitre_tactic} techniqueId={alert.mitre_technique_id} />
  </td>
  <td className="px-4 py-3">
    <StatusBadge status={alert.status} />
  </td>
</tr>
```

---

### AI Explanation Card

```tsx
<div className="
  bg-slate-800 border border-slate-700
  rounded-lg p-6
">
  <div className="flex items-center gap-2 mb-3">
    <Sparkles className="w-4 h-4 text-blue-400" aria-hidden="true" />
    <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wide">
      AI Analysis
    </h3>
    <span className="ml-auto text-xs text-slate-500">
      Powered by Claude
    </span>
  </div>

  {/* Loading state */}
  {isLoading && (
    <div className="space-y-2 animate-pulse">
      <div className="h-4 bg-slate-700 rounded w-full" />
      <div className="h-4 bg-slate-700 rounded w-5/6" />
      <div className="h-4 bg-slate-700 rounded w-4/6" />
    </div>
  )}

  {/* Explanation text */}
  {explanation && (
    <p className="text-base text-slate-200 leading-relaxed">
      {explanation}
    </p>
  )}

  {/* Error state */}
  {error && (
    <p className="text-sm text-slate-400 italic">
      Explanation unavailable. AI service unreachable.{" "}
      <button onClick={retry} className="text-blue-400 hover:underline">
        Retry
      </button>
    </p>
  )}

  {/* Feedback */}
  {explanation && (
    <div className="flex items-center gap-3 mt-4 pt-4 border-t border-slate-700">
      <span className="text-xs text-slate-500">Was this helpful?</span>
      <button
        onClick={() => submitFeedback("helpful")}
        className="text-xs text-slate-400 hover:text-green-400 flex items-center gap-1"
        aria-label="Mark explanation as helpful"
      >
        <ThumbsUp className="w-3.5 h-3.5" /> Yes
      </button>
      <button
        onClick={() => submitFeedback("not_helpful")}
        className="text-xs text-slate-400 hover:text-red-400 flex items-center gap-1"
        aria-label="Mark explanation as not helpful"
      >
        <ThumbsDown className="w-3.5 h-3.5" /> No
      </button>
    </div>
  )}
</div>
```

---

### KPI Summary Card

```tsx
<div className="
  bg-slate-800 border border-slate-700
  rounded-lg p-6
">
  <div className="flex items-center justify-between mb-2">
    <span className="text-sm text-slate-400">{label}</span>
    <Icon className="w-4 h-4 text-slate-500" aria-hidden="true" />
  </div>
  <div className="flex items-end gap-2">
    <span className={`text-3xl font-bold ${valueColor}`}>
      {value}
    </span>
    {trend && (
      <span className={`text-sm mb-1 ${trend > 0 ? "text-red-400" : "text-green-400"}`}>
        {trend > 0 ? "↑" : "↓"} {Math.abs(trend)}%
      </span>
    )}
  </div>
  {sublabel && (
    <p className="text-xs text-slate-500 mt-1">{sublabel}</p>
  )}
</div>
```

---

### Primary Button

```tsx
<button
  className="
    inline-flex items-center gap-2
    px-4 py-2
    bg-blue-600 hover:bg-blue-500
    text-white text-sm font-medium
    rounded-lg
    transition-colors duration-150
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900
    disabled:opacity-50 disabled:cursor-not-allowed
  "
  disabled={isLoading}
>
  {isLoading ? (
    <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
  ) : (
    <Icon className="w-4 h-4" aria-hidden="true" />
  )}
  {label}
</button>
```

---

### Danger Button (for Escalate, destructive actions)

```tsx
<button
  className="
    inline-flex items-center gap-2
    px-4 py-2
    bg-red-600 hover:bg-red-500
    text-white text-sm font-medium
    rounded-lg
    transition-colors duration-150
    focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-slate-900
  "
>
  <AlertTriangle className="w-4 h-4" aria-hidden="true" />
  Escalate
</button>
```

---

### Ghost Button (for Dismiss, secondary actions)

```tsx
<button
  className="
    inline-flex items-center gap-2
    px-4 py-2
    bg-transparent hover:bg-slate-700
    text-slate-300 hover:text-slate-100 text-sm font-medium
    border border-slate-600 hover:border-slate-500
    rounded-lg
    transition-colors duration-150
    focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-slate-900
  "
>
  {label}
</button>
```

---

### Modal

```tsx
{/* Overlay */}
<div
  className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4"
  onClick={onClose}
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
>
  {/* Modal panel */}
  <div
    className="
      relative
      bg-slate-800 border border-slate-700
      rounded-xl shadow-lg
      p-6 w-full max-w-md
    "
    onClick={(e) => e.stopPropagation()}
  >
    <div className="flex items-center justify-between mb-4">
      <h2 id="modal-title" className="text-lg font-semibold text-slate-100">
        {title}
      </h2>
      <button
        onClick={onClose}
        className="text-slate-400 hover:text-slate-200"
        aria-label="Close modal"
      >
        <X className="w-5 h-5" />
      </button>
    </div>

    {children}

    <div className="flex gap-3 justify-end mt-6 pt-4 border-t border-slate-700">
      <GhostButton onClick={onClose}>Cancel</GhostButton>
      <PrimaryButton onClick={onConfirm}>{confirmLabel}</PrimaryButton>
    </div>
  </div>
</div>
```

---

### Text Input

```tsx
<div className="space-y-1.5">
  <label
    htmlFor={id}
    className="block text-sm font-medium text-slate-300"
  >
    {label}
    {required && <span className="text-red-400 ml-1" aria-label="required">*</span>}
  </label>
  <input
    id={id}
    type={type}
    className="
      block w-full
      px-3 py-2
      bg-slate-900 border border-slate-600
      text-slate-100 placeholder:text-slate-500
      rounded-md text-sm
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
      disabled:opacity-50 disabled:cursor-not-allowed
      aria-invalid:border-red-500 aria-invalid:focus:ring-red-500
    "
    aria-invalid={!!error}
    aria-describedby={error ? `${id}-error` : undefined}
    {...props}
  />
  {error && (
    <p id={`${id}-error`} className="text-xs text-red-400 flex items-center gap-1">
      <AlertCircle className="w-3 h-3" aria-hidden="true" />
      {error}
    </p>
  )}
</div>
```

---

### Raw Event JSON Viewer

```tsx
<div className="
  bg-slate-950 border border-slate-800
  rounded-lg p-4 overflow-auto max-h-64
">
  <div className="flex items-center justify-between mb-2">
    <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">
      Raw Event
    </span>
    <button
      onClick={() => copyToClipboard(JSON.stringify(event, null, 2))}
      className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1"
      aria-label="Copy raw event to clipboard"
    >
      <Copy className="w-3 h-3" />
      Copy
    </button>
  </div>
  <pre className="font-mono text-xs text-green-400 whitespace-pre-wrap break-all">
    {JSON.stringify(event, null, 2)}
  </pre>
</div>
```

---

### Toast Notification

```tsx
// Variants: "success" | "error" | "info" | "warning"
const toastConfig = {
  success: { icon: CheckCircle, classes: "bg-green-950 border-green-800 text-green-300" },
  error:   { icon: XCircle,     classes: "bg-red-950 border-red-800 text-red-300" },
  info:    { icon: Info,        classes: "bg-blue-950 border-blue-800 text-blue-300" },
  warning: { icon: AlertTriangle, classes: "bg-yellow-950 border-yellow-800 text-yellow-300" },
};

<div
  role="alert"
  aria-live="polite"
  className={`
    flex items-start gap-3
    px-4 py-3
    rounded-lg border text-sm
    shadow-lg
    ${toastConfig[variant].classes}
  `}
>
  <ToastIcon className="w-4 h-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
  <div>
    <p className="font-medium">{title}</p>
    {description && <p className="mt-0.5 opacity-80">{description}</p>}
  </div>
  <button onClick={dismiss} className="ml-auto opacity-60 hover:opacity-100" aria-label="Dismiss">
    <X className="w-4 h-4" />
  </button>
</div>
```

---

### Empty State

```tsx
<div className="flex flex-col items-center justify-center py-16 text-center">
  <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mb-4">
    <Icon className="w-6 h-6 text-slate-500" aria-hidden="true" />
  </div>
  <h3 className="text-base font-medium text-slate-300 mb-1">{title}</h3>
  <p className="text-sm text-slate-500 max-w-sm">{description}</p>
  {action && (
    <PrimaryButton className="mt-4" onClick={action.onClick}>
      {action.label}
    </PrimaryButton>
  )}
</div>
```

Example: "All clear" state on dashboard — Icon: ShieldCheck, Title: "No active alerts", Description: "All alerts have been triaged. Great work."

---

### Skeleton Loader

```tsx
// For alert table rows during initial load
<div className="animate-pulse">
  {Array.from({ length: 8 }).map((_, i) => (
    <div key={i} className="flex gap-4 px-4 py-3 border-b border-slate-800">
      <div className="h-4 bg-slate-700 rounded w-32" />     {/* timestamp */}
      <div className="h-4 bg-slate-700 rounded w-16" />     {/* severity */}
      <div className="h-4 bg-slate-700 rounded w-28" />     {/* source IP */}
      <div className="h-4 bg-slate-700 rounded w-48" />     {/* event type */}
      <div className="h-4 bg-slate-700 rounded w-36" />     {/* MITRE */}
      <div className="h-4 bg-slate-700 rounded w-20" />     {/* status */}
    </div>
  ))}
</div>
```

---

## 5. Accessibility Guidelines

### WCAG 2.1 Level AA Requirements

- **Color contrast**: Text 4.5:1 minimum. All severity badge text passes on their dark backgrounds.
- **Severity communication**: ALWAYS use icon + text + color. Never color alone.
- **Focus indicators**: 2px ring in blue-500, offset 2px. Visible on dark backgrounds.
- **Keyboard navigation**: All alerts keyboard-navigable (arrow keys in table, Enter to open, Escape to close modals)
- **Screen readers**: All severity badges have `role="status"` and `aria-label`. Alert table has `role="grid"`. Modals have `role="dialog"` with `aria-modal` and `aria-labelledby`.
- **Live regions**: New alerts announced via `aria-live="polite"` region in dashboard header
- **Form errors**: Linked via `aria-describedby`; marked with `aria-invalid`
- **Timestamps**: Display relative time (e.g. "3 min ago") with `<time datetime="ISO8601">` for screen readers

---

## 6. Icon System

- **Library**: Lucide React 0.312.0
- **Sizes**: 16px (inline/table), 20px (buttons/cards), 24px (section headers)
- **Stroke width**: 1.5px default

Key icons used:

```tsx
import {
  AlertOctagon,    // Critical severity
  AlertTriangle,   // High severity / escalate
  AlertCircle,     // Medium severity / form errors
  Info,            // Low severity
  Shield,          // App logo / security context
  ShieldCheck,     // All clear / healthy state
  ShieldAlert,     // Threat detected
  Activity,        // Live / streaming
  Eye,             // Investigate
  XCircle,         // Dismiss / error
  CheckCircle,     // Resolved / success
  ExternalLink,    // MITRE links / external references
  Copy,            // Copy to clipboard
  Download,        // Export
  Filter,          // Filter controls
  Search,          // Search
  Sparkles,        // AI explanation
  RefreshCw,       // Retry / reload
  Clock,           // Timestamps
  Globe,           // IP geolocation
  Loader2,         // Loading spinner (animated with animate-spin)
} from "lucide-react"
```

---

## 7. Animation Guidelines

- Default transition: `transition-colors duration-150 ease-in-out`
- Page transitions: `transition-opacity duration-200`
- Modal: Enter `animate-in fade-in slide-in-from-bottom-4 duration-200`; Exit reverse
- New alert row highlight: `animate-pulse` for 1 second when row first appears
- Skeleton loader shimmer: `animate-pulse`
- Spinner: `animate-spin` on Loader2 icon
- All animations wrapped in `motion-safe:` Tailwind prefix to respect `prefers-reduced-motion`

---

## 8. Tailwind Config

```ts
// tailwind.config.ts
import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",  // Dark mode via class (default: dark)
  theme: {
    extend: {
      colors: {
        critical: { DEFAULT: "#ef4444", bg: "#fef2f2", border: "#fca5a5", text: "#991b1b" },
        high:     { DEFAULT: "#f97316", bg: "#fff7ed", border: "#fdba74", text: "#9a3412" },
        medium:   { DEFAULT: "#eab308", bg: "#fefce8", border: "#fde047", text: "#854d0e" },
        low:      { DEFAULT: "#22c55e", bg: "#f0fdf4", border: "#86efac", text: "#166534" },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 200ms ease-in-out",
        "slide-up": "slideUp 250ms ease-out",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: { from: { transform: "translateY(8px)", opacity: "0" }, to: { transform: "translateY(0)", opacity: "1" } },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
```

---

## 9. Performance Guidelines

- Use `next/image` for all images (logo, geolocation map pins)
- Alert table: virtualize rows with `react-virtual` if alert list exceeds 500 items
- AI explanation: lazy-loaded (only fetched when alert detail opens)
- Charts on Reports page: dynamically imported (`next/dynamic` with `ssr: false`)
- Code split per route — no monolithic bundle
- JSON viewer: dynamically imported (heavy component, rarely needed)
