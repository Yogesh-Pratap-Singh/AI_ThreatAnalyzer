# Application Flow Documentation
# AI Threat Analyzer

**Version**: 1.0  
**Last Updated**: 2026-05-27  

---

## 1. Entry Points

### Primary Entry Points

- **Direct URL** (`https://threats.yourorg.com`): Redirects to `/login` if unauthenticated; redirects to `/dashboard` if session is active
- **Login Page** (`/login`): Email + password form; MFA prompt on success
- **Magic Link Email**: One-click login from email; lands on dashboard
- **API Access** (`/api/v1/...`): JWT bearer token required; used by ingestion agents and integrations

### Secondary Entry Points

- **Alert Email Notification**: "View Alert" link deep-links to `/alerts/:id`
- **Slack Notification** (P1): "Investigate" button deep-links to alert detail
- **PagerDuty Webhook** (P1): Links to alert detail on acknowledgment

---

## 2. Core User Flows

---

### Flow 1: User Login

**Goal**: Authenticate and reach the dashboard  
**Entry Point**: `/login`  
**Frequency**: Once per shift (session lasts 8 hours)

#### Happy Path

1. **Page: Login**
   - Elements: Email input, password input, "Sign In" button, "Forgot password" link
   - User Action: Enters email and password, clicks "Sign In"
   - Validation: Email format check; password non-empty

2. **System Action**: Verifies credentials; checks bcrypt hash; generates JWT access token (15 min) + refresh token (8 hours)

3. **Page: Dashboard**
   - Elements: Alert queue, severity summary cards, real-time feed
   - Success State: User is logged in and viewing live alerts

#### Error States

- **Invalid credentials**: Inline error — "Email or password is incorrect." Form stays filled (email only, password cleared)
- **Account locked** (5 failed attempts): "Account locked for 15 minutes. Check your email for an unlock link."
- **Session expired mid-shift**: Silent background token refresh via refresh token; if refresh token also expired, redirect to `/login` with message "Your session expired. Please sign in again."

#### Edge Cases

- User with MFA enabled (P1): After password, redirect to `/login/mfa` for TOTP code
- User opens two tabs: Both share the same session; both redirect on expiry

---

### Flow 2: Alert Triage (Primary Analyst Workflow)

**Goal**: Review, understand, and act on an alert  
**Entry Point**: Dashboard alert queue  
**Frequency**: 50–200 times per analyst shift

#### Happy Path

1. **Page: Dashboard** (`/dashboard`)
   - Elements: Alert table sorted by severity DESC, severity filter pills, search bar, status filter
   - User Action: Clicks on a "Critical" alert row

2. **Page: Alert Detail** (`/alerts/:id`)
   - Elements: AI explanation card, severity badge, MITRE tactic badge, source IP + geolocation, raw event panel, related events timeline, action buttons
   - System Action on load: Fetches cached explanation if available; triggers LLM call if not (shows skeleton loader)
   - User reads: AI explanation (< 150 words), MITRE mapping, recommended action

3. **Decision: Analyst chooses action**
   - → Escalate: Opens escalation modal
   - → Dismiss: Opens dismiss modal
   - → Mark False Positive: One-click with optional note
   - → Add Note: Inline note editor

4. **Modal: Escalate**
   - Elements: Priority selector (P1/P2/P3), assignee dropdown, notes textarea, "Escalate" button
   - User Action: Selects priority, adds note, clicks Escalate
   - System Action: Updates alert status to "Escalated"; timestamps; notifies assignee

5. **Page: Dashboard** (returns after action)
   - Alert removed from active queue (if dismissed/escalated)
   - Toast: "Alert escalated to Marcus Chen"

#### Error States

- **LLM explanation times out (> 15s)**: Show "Explanation generating… this may take a moment" with a retry button; raw event data still shown so analyst isn't blocked
- **Alert already actioned by another analyst**: Show banner: "Aisha Chen escalated this alert 2 minutes ago." Action buttons disabled
- **No geolocation data for IP**: Show "Location unavailable" — do not block the rest of the view

#### Edge Cases

- Analyst opens same alert in two browser tabs: Second tab shows stale state; on action, refreshes and shows current state
- Alert is updated while analyst is reading it (e.g., new related events arrive): Show "New events detected — refresh to update" banner; do not auto-refresh and disrupt reading

---

### Flow 3: False Positive Dismissal & Feedback

**Goal**: Dismiss a low-value alert and submit feedback to improve the model  
**Entry Point**: Alert Detail page  
**Frequency**: ~30% of alerts (based on estimated false positive rate)

#### Happy Path

1. **Alert Detail Page**: Analyst reviews AI explanation and determines alert is benign
2. User clicks "Mark as False Positive"
3. **Modal: False Positive Feedback**
   - Elements: "Why is this a false positive?" dropdown (Scheduled job / Known safe behavior / Asset misconfiguration / Other), notes textarea (optional), "Confirm" button
4. User selects reason, optionally adds note, clicks "Confirm"
5. **System Actions**:
   - Updates alert status to "False Positive"
   - Writes feedback record to `analyst_feedback` table
   - Flags event signature for model retraining queue
6. Dashboard: Alert removed from active queue; toast "Marked as false positive. This will help improve future detections."

#### Error States

- **User submits without selecting a reason**: Inline validation: "Please select a reason before confirming"

---

### Flow 4: Ingestion Source Configuration

**Goal**: Connect a new log source to the system  
**Entry Point**: Settings → Data Sources  
**Frequency**: Rare (setup only)

#### Happy Path

1. **Page: Settings / Data Sources** (`/settings/sources`)
   - Elements: List of active sources with health indicators, "Add Source" button
2. User clicks "Add Source"
3. **Modal: Add Data Source**
   - Step 1: Select type (Syslog / JSON HTTP / CSV Upload)
   - Step 2: Configure (for Syslog: host/port; for HTTP: generate API key; for CSV: upload file)
   - Step 3: Test connection — system sends a test ping
   - Step 4: Name the source and save
4. **Success State**: New source appears in list with "Healthy" badge; ingestion begins within 60 seconds

#### Error States

- **Test connection fails**: Show "Connection failed — check host/port and firewall rules." with troubleshooting link
- **Duplicate source name**: Inline validation: "A source with this name already exists"

---

### Flow 5: Weekly Report Generation (CISO)

**Goal**: Generate and export a weekly threat summary  
**Entry Point**: Reports tab  
**Frequency**: Weekly

#### Happy Path

1. **Page: Reports** (`/reports`)
2. User selects date range (presets: Last 7 days, Last 30 days, Custom)
3. System generates report (< 10 seconds): Alert volume chart, severity breakdown, top MITRE tactics, top source IPs, MTTT trend, false positive rate trend
4. User clicks "Export PDF"
5. **System Action**: Generates PDF via server-side rendering; download starts
6. Success: PDF downloaded

#### Error States

- **No data for selected range**: Show "No alerts in this period" with a chart showing zero-line

---

## 3. Navigation Map

```
/ (root)
├── /login
│   └── /login/mfa (P1)
├── /dashboard (authenticated)
│   └── /alerts/:id (alert detail)
├── /search (authenticated, P1)
├── /reports (authenticated)
│   └── /reports/:id (saved report)
├── /settings (authenticated)
│   ├── /settings/sources (data source management)
│   ├── /settings/thresholds (detection tuning)
│   ├── /settings/users (admin only)
│   └── /settings/profile
└── /admin (admin role only)
    └── /admin/model-health
```

### Navigation Rules

- All routes except `/login` require a valid JWT session
- `/admin/*` requires `role: admin`
- `/settings/users` requires `role: admin`
- Unauthenticated requests redirect to `/login?redirect={original_path}` — after login, redirect to original destination
- Back button on alert detail returns to dashboard at previous scroll position

---

## 4. Screen Inventory

### Screen: Dashboard (`/dashboard`)

- **Route**: `/dashboard`
- **Access**: Authenticated
- **Purpose**: Primary alert triage workspace
- **Key Elements**:
  - Summary cards: Critical count, High count, new in last hour, MTTT today
  - Alert table: Sortable columns (severity, timestamp, source IP, event type, MITRE tactic, status)
  - Filter bar: Severity pills, status dropdown, time range picker, search input
  - Real-time badge: "Live" indicator, last updated timestamp
- **Actions**: Click row → Alert Detail; Filter → updates table; Search → filters table
- **State Variants**: Loading (skeleton rows), Empty (no active alerts — "All clear" illustration), Error (failed to fetch — retry button)

---

### Screen: Alert Detail (`/alerts/:id`)

- **Route**: `/alerts/:id`
- **Access**: Authenticated
- **Purpose**: Full investigation view for a single alert
- **Key Elements**:
  - Header: Alert ID, severity badge, status badge, timestamp
  - AI Explanation card: Plain-language text, helpful/not helpful rating buttons
  - MITRE card: Tactic name, technique ID, confidence score, link to ATT&CK
  - Threat Intel card: Matched IOCs, CVE references (if applicable)
  - Source info: Source IP, geolocation map pin, hostname (if resolved)
  - Raw event panel: JSON viewer, collapsible
  - Related events timeline: Last 24 hours from same source IP
  - Analyst notes: Chronological thread
  - Action bar: Escalate, Dismiss, Mark False Positive, Add Note
- **State Variants**: Explanation loading (skeleton), Explanation error (fallback text + retry), Alert already actioned (read-only mode + banner)

---

### Screen: Login (`/login`)

- **Route**: `/login`
- **Access**: Public
- **Purpose**: Authentication
- **Key Elements**: Email input, password input, Sign In button, Forgot password link
- **State Variants**: Default, Loading (button spinner), Error (inline message)

---

### Screen: Reports (`/reports`)

- **Route**: `/reports`
- **Access**: Authenticated
- **Purpose**: Generate threat summaries and trend analysis
- **Key Elements**: Date range picker, metric cards, charts (alert volume, severity breakdown, MITRE tactics), Export PDF button
- **State Variants**: Loading (chart skeletons), Empty (no data message), Generated (full report)

---

### Screen: Data Sources (`/settings/sources`)

- **Route**: `/settings/sources`
- **Access**: Authenticated (admin for add/remove)
- **Purpose**: Manage log ingestion sources
- **Key Elements**: Sources list with health badges, Add Source button, per-source event rate sparkline
- **State Variants**: Healthy source, Degraded source (amber badge), Disconnected source (red badge + reconnect button)

---

## 5. Decision Points

### Authentication Check (All Routes)

```
IF valid JWT in cookie/header
  AND token not expired
THEN allow access
ELSE IF valid refresh token exists
  THEN silently refresh access token → allow access
ELSE
  THEN redirect to /login?redirect={current_path}
```

### Alert Explanation State

```
IF explanation exists in cache (threat_explanations table)
THEN display cached explanation immediately
ELSE IF LLM API is reachable
  THEN trigger async LLM call → show skeleton → display on completion
ELSE
  THEN show "Explanation unavailable — AI service unreachable. Raw event data shown below."
```

### Alert Action Availability

```
IF alert.status == "open"
  THEN show all action buttons (Escalate, Dismiss, False Positive, Add Note)
ELSE IF alert.status == "escalated" OR "dismissed" OR "false_positive"
  THEN show read-only view + "Reopen" button (admin only)
  AND disable all primary action buttons
```

### Severity Badge Color

```
IF severity_score >= 0.85 THEN badge = Critical (red)
ELSE IF severity_score >= 0.65 THEN badge = High (orange)
ELSE IF severity_score >= 0.40 THEN badge = Medium (yellow)
ELSE THEN badge = Low (green)
```

### Report Export State

```
IF data exists for selected range
  THEN render report + enable Export PDF
ELSE
  THEN show empty state — disable Export PDF
```

---

## 6. Error Handling Flows

### API Unavailable (500 / Network Error)

- Dashboard: Shows error banner at top — "Unable to reach server. Retrying in 30 seconds." Auto-retry with exponential backoff
- Alert Detail: Shows cached data if available; red banner for live data failure
- Action submission failure: Toast — "Action failed. Please try again." Button re-enabled

### 404 — Alert Not Found

- Display: "Alert not found. It may have been deleted or you may not have permission."
- Actions: Back to Dashboard button

### Rate Limited (429)

- Display: Inline — "Too many requests. Please wait a moment before trying again."
- No redirect; user stays on current page

### Session Expired

- Any page: Modal overlay — "Your session has expired. Please sign in again." with Sign In button
- No data loss: Current page URL saved so user returns after re-auth

---

## 7. Responsive Behavior

### Desktop (≥ 1280px) — Primary Target

- Full alert table with all columns visible
- Side-by-side layout on Alert Detail (explanation + raw event)
- Persistent left sidebar navigation

### Tablet (768–1279px)

- Alert table: hide "Raw Event Type" column, keep severity + timestamp + source + MITRE + status
- Alert Detail: stacked layout (explanation above raw event)
- Collapsible sidebar (hamburger trigger)

### Mobile (< 768px) — Read-Only Mode

- Alert list view (cards, not table)
- Alert Detail: minimal view — explanation + severity + action buttons only
- No source configuration or reporting on mobile
- Banner: "Full functionality available on desktop"

---

## 8. Animation & Transitions

| Element | Animation | Duration |
|---------|-----------|----------|
| Page navigation | Fade in | 200ms |
| Modal open | Slide up + fade | 250ms |
| Modal close | Fade out | 150ms |
| Toast notification | Slide in from top-right | 200ms |
| Alert row (new) | Highlight pulse (amber) | 1s, once |
| Skeleton loader | Shimmer | 1.5s loop |
| Severity badge | None — static | — |
| Action button (loading) | Spinner replace icon | Immediate |

All animations respect `prefers-reduced-motion: reduce` — fall back to instant transitions.
