# Backend Architecture & Database Structure
# AI Threat Analyzer

**Version**: 1.0  
**Last Updated**: 2026-05-27  

---

## 1. Architecture Overview

### System Architecture

```
[Log Sources] → [Ingestion API] → [Kafka: raw-events]
                                          ↓
                               [Normalization Worker]
                                          ↓
                               [Kafka: normalized-events]
                                          ↓
                               [Anomaly Scoring Worker]
                                    (IsolationForest)
                                          ↓
                               [Kafka: scored-events]
                                          ↓
                              [Alert Generation Worker]
                              (threshold check + dedup)
                                          ↓
                    ┌─────────────────────────────────┐
                    │         PostgreSQL + pgvector    │
                    │  events / alerts / knowledge_base│
                    └─────────────────────────────────┘
                                          ↓
                               [FastAPI REST API]
                                          ↓
                    ┌─────────────────────────────────┐
                    │        LLM Explanation          │
                    │  RAG(pgvector) → Claude API     │
                    └─────────────────────────────────┘
                                          ↓
                              [Next.js Dashboard]
```

### Authentication Strategy

JWT-based authentication with short-lived access tokens (15 min) and shift-length refresh tokens (8 hours). Tokens stored in HTTP-only Secure cookies. No tokens in `localStorage`.

### Caching Strategy

Redis for: explanation cache (keyed on alert signature hash, 7-day TTL), rate limit counters, SSE connection metadata.

---

## 2. Database Schema

### Database: PostgreSQL 16.1 with pgvector 0.5.1

**ORM**: SQLAlchemy 2.0.25 async  
**Migrations**: Alembic 1.13.1  
**Naming**: snake_case for tables and columns  
**Timestamps**: All tables have `created_at`, `updated_at` (auto-managed)

---

### Table: `users`

**Purpose**: Analyst and admin accounts

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash (12 rounds) |
| full_name | VARCHAR(255) | NOT NULL | Display name |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'analyst' | 'analyst' or 'admin' |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Account enabled flag |
| last_login_at | TIMESTAMP WITH TIME ZONE | NULL | Last successful login |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Account creation |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update |

**Indexes**: `idx_users_email` ON (email)

---

### Table: `sessions`

**Purpose**: Track active refresh tokens (one per login session)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FK → users(id) ON DELETE CASCADE, NOT NULL | Session owner |
| refresh_token_hash | VARCHAR(255) | UNIQUE, NOT NULL | bcrypt hash of refresh token |
| user_agent | TEXT | NULL | Browser/client info |
| ip_address | VARCHAR(45) | NULL | Login IP |
| expires_at | TIMESTAMP WITH TIME ZONE | NOT NULL | Token expiry (8 hours) |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Session start |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last refresh |

**Indexes**:
- `idx_sessions_user_id` ON (user_id)
- `idx_sessions_expires_at` ON (expires_at)

**Cleanup**: Alembic-managed cron job deletes expired sessions daily.

---

### Table: `data_sources`

**Purpose**: Configured log ingestion sources

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| name | VARCHAR(255) | UNIQUE, NOT NULL | Human label (e.g., "prod-firewall-01") |
| source_type | VARCHAR(50) | NOT NULL | 'syslog', 'json_http', 'csv_upload' |
| config_json | JSONB | NOT NULL | Connection config (host, port, api_key, etc.) |
| api_key_hash | VARCHAR(255) | NULL | Hashed API key for json_http sources |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | 'active', 'degraded', 'disconnected' |
| last_event_at | TIMESTAMP WITH TIME ZONE | NULL | Most recent event received |
| events_per_minute | INTEGER | NULL | Rolling 5-min average |
| created_by | UUID | FK → users(id), NOT NULL | Who configured it |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | |

**Indexes**: `idx_sources_status` ON (status)

---

### Table: `events`

**Purpose**: Normalized, stored log events (subset — high-anomaly-score events only; raw stream stays in Kafka)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| source_id | UUID | FK → data_sources(id), NOT NULL | Which source produced this |
| event_time | TIMESTAMP WITH TIME ZONE | NOT NULL | Original event timestamp |
| source_ip | VARCHAR(45) | NULL | Source IP address |
| dest_ip | VARCHAR(45) | NULL | Destination IP |
| source_port | INTEGER | NULL | Source port |
| dest_port | INTEGER | NULL | Destination port |
| protocol | VARCHAR(20) | NULL | tcp, udp, icmp, etc. |
| event_type | VARCHAR(255) | NOT NULL | Normalized event category |
| bytes_transferred | BIGINT | NULL | Bytes in event |
| anomaly_score | FLOAT | NOT NULL | Isolation Forest score (0.0–1.0) |
| raw_payload | JSONB | NOT NULL | Original event as JSON |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Storage timestamp |

**Indexes**:
- `idx_events_source_ip` ON (source_ip)
- `idx_events_event_time` ON (event_time DESC) — BRIN index for time-range queries
- `idx_events_anomaly_score` ON (anomaly_score DESC)
- `idx_events_source_id` ON (source_id)

**Partitioning**: Range-partitioned by `event_time` (monthly partitions), automated via pg_partman.

---

### Table: `alerts`

**Purpose**: Correlated, scored, actionable threat alerts

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| title | VARCHAR(500) | NOT NULL | Auto-generated summary title |
| severity | VARCHAR(20) | NOT NULL | 'critical', 'high', 'medium', 'low' |
| severity_score | FLOAT | NOT NULL | Computed 0.0–1.0 composite score |
| anomaly_score | FLOAT | NOT NULL | Raw ML score component |
| intel_match_score | FLOAT | NOT NULL, DEFAULT 0.0 | Threat intel match component |
| tactic_weight | FLOAT | NOT NULL, DEFAULT 0.0 | MITRE tactic severity component |
| asset_criticality | FLOAT | NOT NULL, DEFAULT 0.5 | Asset importance component |
| source_ip | VARCHAR(45) | NULL | Primary source IP |
| dest_ip | VARCHAR(45) | NULL | Primary destination IP |
| event_type | VARCHAR(255) | NOT NULL | Event category |
| mitre_tactic | VARCHAR(100) | NULL | MITRE ATT&CK tactic name |
| mitre_technique_id | VARCHAR(20) | NULL | e.g., 'T1048.001' |
| mitre_confidence | FLOAT | NULL | Mapping confidence (0.0–1.0) |
| alert_signature | VARCHAR(255) | NOT NULL | Hash of alert pattern (for dedup + cache key) |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'open' | 'open', 'escalated', 'dismissed', 'false_positive', 'resolved' |
| event_count | INTEGER | NOT NULL, DEFAULT 1 | Number of underlying events correlated |
| first_seen_at | TIMESTAMP WITH TIME ZONE | NOT NULL | Earliest event time |
| last_seen_at | TIMESTAMP WITH TIME ZONE | NOT NULL | Most recent event time |
| actioned_by | UUID | FK → users(id) ON DELETE SET NULL, NULL | Who took action |
| actioned_at | TIMESTAMP WITH TIME ZONE | NULL | When action taken |
| escalated_to | UUID | FK → users(id) ON DELETE SET NULL, NULL | Assignee on escalation |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Alert generated |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update |

**Indexes**:
- `idx_alerts_status_severity` ON (status, severity_score DESC) — primary query index
- `idx_alerts_source_ip` ON (source_ip)
- `idx_alerts_created_at` ON (created_at DESC)
- `idx_alerts_signature` ON (alert_signature) UNIQUE (prevents duplicates)
- `idx_alerts_mitre_tactic` ON (mitre_tactic)

---

### Table: `alert_events`

**Purpose**: Junction table linking alerts to their underlying events

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| alert_id | UUID | FK → alerts(id) ON DELETE CASCADE | Parent alert |
| event_id | UUID | FK → events(id) ON DELETE CASCADE | Contributing event |
| PRIMARY KEY | (alert_id, event_id) | | Composite key |

**Indexes**: `idx_alert_events_alert_id` ON (alert_id)

---

### Table: `threat_explanations`

**Purpose**: Cached LLM-generated threat explanations (keyed on alert signature)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | |
| alert_signature | VARCHAR(255) | UNIQUE, NOT NULL | Matches alerts.alert_signature |
| explanation_text | TEXT | NOT NULL | Plain-language threat explanation |
| mitre_tactic | VARCHAR(100) | NULL | Extracted MITRE tactic |
| mitre_technique_id | VARCHAR(20) | NULL | Extracted technique ID |
| recommended_action | TEXT | NULL | Extracted recommended next step |
| model_used | VARCHAR(100) | NOT NULL | e.g., 'claude-sonnet-4-6' |
| prompt_version | INTEGER | NOT NULL, DEFAULT 1 | Prompt template version |
| helpful_count | INTEGER | NOT NULL, DEFAULT 0 | Analyst thumbs-up count |
| not_helpful_count | INTEGER | NOT NULL, DEFAULT 0 | Analyst thumbs-down count |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | |
| expires_at | TIMESTAMP WITH TIME ZONE | NOT NULL | Cache expiry (7 days) |

**Indexes**: `idx_explanations_signature` ON (alert_signature)

---

### Table: `analyst_notes`

**Purpose**: Analyst notes attached to alerts

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | |
| alert_id | UUID | FK → alerts(id) ON DELETE CASCADE, NOT NULL | Parent alert |
| user_id | UUID | FK → users(id) ON DELETE SET NULL | Note author |
| content | TEXT | NOT NULL | Note text |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | |

**Indexes**: `idx_notes_alert_id` ON (alert_id)

---

### Table: `analyst_feedback`

**Purpose**: False positive and explanation quality feedback for model retraining

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | |
| alert_id | UUID | FK → alerts(id) ON DELETE CASCADE, NOT NULL | Actioned alert |
| user_id | UUID | FK → users(id) ON DELETE SET NULL | Analyst |
| feedback_type | VARCHAR(30) | NOT NULL | 'false_positive', 'explanation_helpful', 'explanation_not_helpful' |
| fp_reason | VARCHAR(100) | NULL | 'scheduled_job', 'known_safe', 'misconfiguration', 'other' |
| notes | TEXT | NULL | Free text |
| alert_signature | VARCHAR(255) | NOT NULL | Copied for ML pipeline use |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | |

**Indexes**: `idx_feedback_alert_signature` ON (alert_signature)

---

### Table: `knowledge_base`

**Purpose**: RAG knowledge base — MITRE ATT&CK techniques and CVEs, stored as embeddings

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | |
| source_type | VARCHAR(50) | NOT NULL | 'mitre_attack', 'cve', 'threat_report' |
| source_id | VARCHAR(50) | NOT NULL | e.g., 'T1048.001', 'CVE-2024-1234' |
| title | VARCHAR(500) | NOT NULL | Technique/CVE name |
| content | TEXT | NOT NULL | Full description text |
| embedding | vector(384) | NOT NULL | all-MiniLM-L6-v2 embedding |
| metadata_json | JSONB | NOT NULL, DEFAULT '{}' | Tactics, severity, references |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | |

**Indexes**: `idx_knowledge_embedding` using `ivfflat` ON (embedding vector_cosine_ops) WITH (lists = 100)

---

## 3. API Endpoints

All endpoints prefixed with `/api/v1/`

---

### Authentication: `POST /api/v1/auth/login`

**Purpose**: Authenticate user, return JWT tokens

**Request Body**:
```json
{
  "email": "analyst@yourorg.com",
  "password": "SecureP@ss123"
}
```

**Validation**:
- email: valid format, max 255 chars
- password: non-empty, max 128 chars

**Response (200)**:
```json
{
  "user": {
    "id": "uuid",
    "email": "analyst@yourorg.com",
    "full_name": "Aisha Patel",
    "role": "analyst"
  }
}
```

**Cookies Set**:
- `access_token`: HTTP-only, Secure, SameSite=Strict, Max-Age=900 (15 min)
- `refresh_token`: HTTP-only, Secure, SameSite=Strict, Max-Age=28800 (8 hours)

**Errors**:
- 401: Invalid credentials
- 403: Account inactive
- 429: Rate limited (5 attempts per 15 min per IP)

**Side Effects**: Updates `last_login_at`; creates `sessions` record

---

### Authentication: `POST /api/v1/auth/refresh`

**Purpose**: Get new access token using refresh token cookie

**Cookies Required**: `refresh_token`

**Response (200)**:
```json
{ "ok": true }
```

Sets new `access_token` cookie.

**Errors**: 401 if refresh token invalid or expired

---

### Authentication: `POST /api/v1/auth/logout`

**Purpose**: Invalidate session

**Auth Required**: Yes

**Response (200)**: `{ "ok": true }`

**Side Effects**: Deletes session from `sessions` table; clears both cookies

---

### Alerts: `GET /api/v1/alerts`

**Purpose**: List alerts with filtering and pagination

**Auth Required**: Yes

**Query Parameters**:
- `page` (int, default: 1)
- `limit` (int, default: 50, max: 200)
- `severity` (string, comma-separated: `critical,high`)
- `status` (string, default: `open`)
- `source_ip` (string, optional)
- `mitre_tactic` (string, optional)
- `from_time` (ISO8601, optional)
- `to_time` (ISO8601, optional)
- `sort` (string: `severity_desc` | `created_at_desc`, default: `severity_desc`)

**Response (200)**:
```json
{
  "alerts": [
    {
      "id": "uuid",
      "title": "Unusual outbound traffic to Tor exit node",
      "severity": "critical",
      "severity_score": 0.91,
      "source_ip": "10.0.1.44",
      "dest_ip": "185.220.101.45",
      "event_type": "outbound_transfer",
      "mitre_tactic": "Exfiltration",
      "mitre_technique_id": "T1048",
      "status": "open",
      "event_count": 12,
      "first_seen_at": "2026-05-27T02:14:00Z",
      "last_seen_at": "2026-05-27T02:18:33Z",
      "created_at": "2026-05-27T02:19:01Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 143,
    "pages": 3
  }
}
```

**Caching**: SSE-driven — no HTTP cache. TanStack Query polls every 5 seconds as fallback.

---

### Alerts: `GET /api/v1/alerts/:id`

**Purpose**: Get full alert detail including related events

**Auth Required**: Yes

**Response (200)**:
```json
{
  "alert": {
    "id": "uuid",
    "title": "...",
    "severity": "critical",
    "severity_score": 0.91,
    "severity_breakdown": {
      "anomaly_score": 0.94,
      "intel_match_score": 0.85,
      "tactic_weight": 0.90,
      "asset_criticality": 0.75
    },
    "source_ip": "10.0.1.44",
    "dest_ip": "185.220.101.45",
    "source_port": 52341,
    "dest_port": 443,
    "event_type": "outbound_transfer",
    "bytes_transferred": 2468000000,
    "mitre_tactic": "Exfiltration",
    "mitre_technique_id": "T1048",
    "mitre_technique_name": "Exfiltration Over Alternative Protocol",
    "mitre_confidence": 0.87,
    "mitre_url": "https://attack.mitre.org/techniques/T1048",
    "status": "open",
    "event_count": 12,
    "first_seen_at": "2026-05-27T02:14:00Z",
    "last_seen_at": "2026-05-27T02:18:33Z",
    "notes": [],
    "explanation": null,
    "created_at": "2026-05-27T02:19:01Z"
  },
  "related_events": [
    {
      "id": "uuid",
      "event_time": "2026-05-27T02:14:11Z",
      "event_type": "outbound_transfer",
      "bytes_transferred": 205000000,
      "anomaly_score": 0.94
    }
  ]
}
```

**Errors**: 404 if alert not found; 403 if user lacks permission

---

### Alerts: `GET /api/v1/alerts/:id/explanation`

**Purpose**: Get or generate AI threat explanation for an alert

**Auth Required**: Yes

**Logic**:
1. Check `threat_explanations` table for matching `alert_signature`
2. If found and not expired → return cached explanation
3. If not found → run RAG + LLM pipeline → cache result → return

**Response (200)**:
```json
{
  "explanation": "Host 10.0.1.44 (Finance-Workstation-07) transferred 2.3 GB to IP 185.220.101.45, a known Tor exit node in Romania, over port 443 in a 4-minute window — 47× above baseline for this host. This pattern is consistent with T1048 (Exfiltration Over Alternative Protocol), where data is exfiltrated via encrypted channels to avoid detection. Recommended action: immediately isolate the host and initiate forensic capture of network traffic for the past 24 hours.",
  "mitre_tactic": "Exfiltration",
  "mitre_technique_id": "T1048",
  "recommended_action": "Isolate host and capture network traffic for forensic analysis",
  "cached": false,
  "model_used": "claude-sonnet-4-6"
}
```

**Errors**:
- 503: LLM API unreachable (returns partial response with `explanation: null`)
- 404: Alert not found

**Side Effects**: Writes to `threat_explanations` table; caches in Redis with 7-day TTL

---

### Alerts: `PATCH /api/v1/alerts/:id/action`

**Purpose**: Perform a triage action on an alert

**Auth Required**: Yes

**Request Body**:
```json
{
  "action": "escalate",
  "priority": "P1",
  "assignee_id": "uuid",
  "note": "Possible data exfiltration — isolating host"
}
```

Valid `action` values: `escalate`, `dismiss`, `false_positive`, `resolve`

**Validation**:
- `action`: required, enum
- `assignee_id`: required when action = `escalate`
- `priority`: required when action = `escalate`; values: `P1`, `P2`, `P3`
- `note`: optional, max 2000 chars

**Response (200)**:
```json
{
  "alert_id": "uuid",
  "status": "escalated",
  "actioned_by": "uuid",
  "actioned_at": "2026-05-27T02:22:15Z"
}
```

**Errors**:
- 409: Alert already actioned (returns current state)
- 422: Invalid action for current status

**Side Effects**: Updates alert status; creates `analyst_notes` record if note provided; triggers email notification to assignee if `escalate`

---

### Alerts: `POST /api/v1/alerts/:id/notes`

**Purpose**: Add a note to an alert

**Auth Required**: Yes

**Request Body**:
```json
{ "content": "Confirmed with IT — this is the scheduled backup job." }
```

**Validation**: content: 1–2000 chars

**Response (201)**:
```json
{
  "id": "uuid",
  "alert_id": "uuid",
  "user": { "id": "uuid", "full_name": "Aisha Patel" },
  "content": "Confirmed with IT — this is the scheduled backup job.",
  "created_at": "2026-05-27T02:25:00Z"
}
```

---

### Feedback: `POST /api/v1/feedback`

**Purpose**: Submit analyst feedback for model retraining

**Auth Required**: Yes

**Request Body**:
```json
{
  "alert_id": "uuid",
  "feedback_type": "false_positive",
  "fp_reason": "scheduled_job",
  "notes": "Weekly backup runs Sunday nights"
}
```

**Validation**:
- `feedback_type`: enum — `false_positive`, `explanation_helpful`, `explanation_not_helpful`
- `fp_reason`: required when `feedback_type = false_positive`
- `notes`: optional, max 1000 chars

**Response (201)**: `{ "ok": true }`

**Side Effects**: Writes to `analyst_feedback`; increments `helpful_count` or `not_helpful_count` on `threat_explanations` if applicable

---

### Ingestion: `POST /api/v1/ingest/events`

**Purpose**: Accept JSON log events from configured sources

**Auth**: API key in `X-Source-API-Key` header (no JWT — used by agents)

**Request Body**:
```json
{
  "source_id": "uuid",
  "events": [
    {
      "timestamp": "2026-05-27T02:14:11Z",
      "source_ip": "10.0.1.44",
      "dest_ip": "185.220.101.45",
      "source_port": 52341,
      "dest_port": 443,
      "protocol": "tcp",
      "event_type": "network_connection",
      "bytes": 205000000,
      "raw": { "...original log fields..." }
    }
  ]
}
```

**Validation**: Max 1000 events per request; source_id must match valid data source; API key must match source config

**Response (202)**: `{ "accepted": 847 }` — async; events queued to Kafka

**Rate Limit**: 10,000 events/minute per source key

---

### Reports: `GET /api/v1/reports/summary`

**Purpose**: Generate threat summary for a date range

**Auth Required**: Yes

**Query Parameters**:
- `from_time` (ISO8601, required)
- `to_time` (ISO8601, required)

**Response (200)**:
```json
{
  "period": { "from": "2026-05-20T00:00:00Z", "to": "2026-05-27T00:00:00Z" },
  "total_alerts": 1247,
  "by_severity": { "critical": 3, "high": 42, "medium": 318, "low": 884 },
  "false_positive_rate": 0.18,
  "mean_triage_time_minutes": 18,
  "top_mitre_tactics": [
    { "tactic": "Initial Access", "count": 423 },
    { "tactic": "Exfiltration", "count": 89 }
  ],
  "top_source_ips": [
    { "ip": "10.0.1.44", "alert_count": 12 }
  ],
  "alert_volume_by_day": [
    { "date": "2026-05-20", "count": 167 }
  ]
}
```

---

### SSE: `GET /api/v1/alerts/stream`

**Purpose**: Server-Sent Events stream for real-time new alerts

**Auth Required**: Yes (JWT in cookie)

**Response**: `text/event-stream`

```
event: new_alert
data: {"id":"uuid","severity":"critical","title":"...","source_ip":"...","created_at":"..."}

event: alert_updated
data: {"id":"uuid","status":"escalated"}

event: heartbeat
data: {}
```

**Reconnect**: Client auto-reconnects on disconnect with `Last-Event-ID` header

---

## 4. LLM Explanation Pipeline

### RAG + Prompt Flow

```python
async def generate_explanation(alert: Alert) -> str:
    # 1. Build query from alert features
    query = f"{alert.event_type} {alert.source_ip} to {alert.dest_ip} port {alert.dest_port}"

    # 2. Retrieve top-5 relevant MITRE/CVE entries via pgvector cosine similarity
    embedding = embed_text(query)  # all-MiniLM-L6-v2
    relevant_intel = await db.execute(
        "SELECT title, content FROM knowledge_base "
        "ORDER BY embedding <=> $1 LIMIT 5",
        embedding
    )

    # 3. Build structured prompt
    system_prompt = """You are a senior cybersecurity analyst. 
    Given an alert and relevant threat intelligence, produce a concise explanation.
    Respond ONLY with a JSON object with fields:
    - explanation: string (max 150 words, plain English)
    - mitre_tactic: string (tactic name)
    - mitre_technique_id: string (e.g. "T1048.001")
    - recommended_action: string (one clear next step)"""

    user_content = {
        "alert": {
            "source_ip": alert.source_ip,
            "dest_ip": alert.dest_ip,
            "dest_port": alert.dest_port,
            "event_type": alert.event_type,
            "bytes_transferred": alert.bytes_transferred,
            "anomaly_score": alert.anomaly_score,
            "first_seen": alert.first_seen_at.isoformat(),
            "last_seen": alert.last_seen_at.isoformat(),
        },
        "threat_intel": [
            {"title": row.title, "content": row.content[:500]}
            for row in relevant_intel
        ]
    }

    # 4. Call Claude API
    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": json.dumps(user_content)}]
    )

    return json.loads(response.content[0].text)
```

---

## 5. Authentication & Authorization

### JWT Token Structure

**Access Token** (15 min):
```json
{
  "sub": "user_uuid",
  "email": "analyst@yourorg.com",
  "role": "analyst",
  "iat": 1748304000,
  "exp": 1748304900
}
```

**Refresh Token** (8 hours):
```json
{
  "sub": "user_uuid",
  "session_id": "session_uuid",
  "iat": 1748304000,
  "exp": 1748332800
}
```

### Authorization Levels

**Public** (no auth): `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/health`

**Authenticated** (any valid JWT): All alert, feedback, report, and ingest endpoints

**Admin only** (`role: admin`): `DELETE /api/v1/users/:id`, `GET /api/v1/admin/model-health`, `POST /api/v1/admin/retrain`

**Source API key** (no JWT): `POST /api/v1/ingest/events`

---

## 6. Severity Scoring Formula

```python
def compute_severity_score(
    anomaly_score: float,       # IsolationForest output, 0–1
    intel_match_score: float,   # IOC/CVE match confidence, 0–1
    tactic_weight: float,       # MITRE tactic base severity, 0–1
    asset_criticality: float,   # Asset importance, 0–1, default 0.5
) -> float:
    score = (
        anomaly_score    * 0.40 +
        intel_match_score * 0.30 +
        tactic_weight    * 0.20 +
        asset_criticality * 0.10
    )
    return round(min(max(score, 0.0), 1.0), 4)

def score_to_severity(score: float) -> str:
    if score >= 0.85: return "critical"
    if score >= 0.65: return "high"
    if score >= 0.40: return "medium"
    return "low"
```

MITRE tactic weights:
```python
TACTIC_WEIGHTS = {
    "Exfiltration": 0.90,
    "Impact": 0.90,
    "Command and Control": 0.85,
    "Lateral Movement": 0.80,
    "Privilege Escalation": 0.75,
    "Persistence": 0.70,
    "Credential Access": 0.70,
    "Defense Evasion": 0.65,
    "Discovery": 0.40,
    "Reconnaissance": 0.35,
    "Initial Access": 0.60,
    "Execution": 0.65,
    "Collection": 0.55,
}
```

---

## 7. Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "ALERT_ALREADY_ACTIONED",
    "message": "This alert was already escalated by Aisha Patel 2 minutes ago.",
    "detail": {
      "current_status": "escalated",
      "actioned_by": "Aisha Patel",
      "actioned_at": "2026-05-27T02:22:15Z"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request body fails validation |
| UNAUTHORIZED | 401 | Missing or invalid JWT |
| FORBIDDEN | 403 | Insufficient role permissions |
| NOT_FOUND | 404 | Resource does not exist |
| ALERT_ALREADY_ACTIONED | 409 | Alert already has a final status |
| RATE_LIMITED | 429 | Too many requests |
| LLM_UNAVAILABLE | 503 | Anthropic API unreachable |
| SERVER_ERROR | 500 | Unexpected server error |

---

## 8. Rate Limiting

| Endpoint | Limit | Window | Key |
|----------|-------|--------|-----|
| POST /auth/login | 5 | 15 min | Per IP |
| All authenticated endpoints | 200 | 1 min | Per user ID |
| POST /ingest/events | 10,000 events | 1 min | Per source API key |
| GET /alerts/stream (SSE) | 5 concurrent | — | Per user ID |

Implementation: Redis sliding window counters. Response on limit: HTTP 429 with `Retry-After` header.

---

## 9. Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "add_asset_criticality_to_alerts"

# Apply to dev
alembic upgrade head

# Apply to staging / production
alembic upgrade head   # run via deploy pipeline, never manually in production

# Rollback one step
alembic downgrade -1
```

**Rules**:
- Never edit a migration file after it has been applied to staging
- Every migration must have a `downgrade()` function
- Test `downgrade` locally before merging
- Migrations run automatically in the deploy pipeline before the new API version starts

---

## 10. Backup & Recovery

- **Frequency**: Automated daily snapshot at 02:00 UTC via AWS RDS automated backups
- **Retention**: 30 days
- **Point-in-Time Recovery**: Enabled (WAL archiving to S3)
- **Recovery Test**: Monthly restore drill to staging environment

**Recovery steps**:
1. Create RDS instance from snapshot
2. Apply any WAL logs needed for point-in-time recovery
3. Update `DATABASE_URL` env var in EKS secrets
4. Run `alembic upgrade head` to verify schema is current
5. Smoke test: login, list alerts, generate explanation
