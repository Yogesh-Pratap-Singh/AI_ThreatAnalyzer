# Product Requirements Document (PRD)
# AI Threat Analyzer — Cybersecurity Intelligence Platform

**Version**: 1.0  
**Last Updated**: 2026-05-27  
**Owner**: Security Engineering Team  

---

## 1. Problem Statement

Security Operations Center (SOC) analysts are overwhelmed. Modern enterprise environments generate millions of log events per day, yet most SIEM tools surface hundreds of undifferentiated alerts — the majority of which are false positives. Analysts spend 50–70% of their time manually correlating events, looking up CVEs, and writing incident summaries, leaving little time for proactive threat hunting.

The core problem: **existing tools detect anomalies but cannot explain them**. An analyst sees "unusual outbound traffic from 10.0.1.44" but must manually investigate whether this is C2 communication, data exfiltration, or a misconfigured backup job. This investigation can take 30–90 minutes per alert. With 200+ alerts per shift, triage becomes impossible.

This platform solves that by combining statistical anomaly detection with LLM-powered threat reasoning — so every alert arrives with a plain-language explanation, a MITRE ATT&CK mapping, a confidence score, and a recommended next action.

---

## 2. Goals & Objectives

### Business Goals

- Reduce mean time to triage (MTTT) by 50% within 90 days of deployment
- Reduce analyst false-positive investigation time by 60%
- Enable a team of 3 analysts to cover what previously required 6
- Achieve 95% analyst satisfaction score on alert explanation quality

### User Goals

- Understand what a threat is and why it matters within 30 seconds of seeing an alert
- Have a clear recommended next action for every high/critical alert
- Be able to dismiss low-confidence alerts with one click and minimal cognitive load
- Search and filter alerts by severity, source, tactic, and time range

---

## 3. Success Metrics

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| Mean time to triage (MTTT) | 45 min | < 22 min | Timestamp: alert created → analyst action |
| False positive dismissal rate | 65% manual review | < 20% manual review | Dismissed alerts / total alerts |
| Alert explanation accuracy | N/A | ≥ 90% analyst rating "helpful" | Post-action feedback survey |
| System alert throughput | N/A | ≥ 10,000 events/min | Load test benchmark |
| Dashboard load time | N/A | < 2 seconds | Lighthouse / synthetic monitoring |
| Analyst coverage ratio | 1:200 alerts | 1:500 alerts | Alerts handled per analyst per shift |

---

## 4. Target Users & Personas

### Primary Persona: Tier 1 SOC Analyst — "Aisha"

- **Role**: Junior security analyst, 1–2 years experience
- **Daily Task**: Monitor alert queue, triage and escalate threats
- **Pain Points**: Overwhelmed by volume; lacks deep threat intel context; slow to identify MITRE tactics; writes incident reports manually
- **Goals**: Clear signal-to-noise ratio; fast triage; confidence in decisions; good documentation trail
- **Technical Proficiency**: Intermediate — comfortable with SIEM dashboards, basic Linux, some scripting
- **Success State**: Can triage 3× more alerts per shift without increased stress

### Secondary Persona: Tier 2 Security Engineer — "Marcus"

- **Role**: Senior analyst / threat hunter, 5+ years experience
- **Daily Task**: Investigate escalated incidents, tune detection rules, review model outputs
- **Pain Points**: Spends too much time reviewing Tier 1 escalations that turn out to be benign; wants to trust AI outputs but needs explainability
- **Goals**: Validate AI reasoning; tune false positive suppression; build custom detection rules; export forensic reports
- **Technical Proficiency**: Advanced — Python, SQL, network forensics, threat intel platforms
- **Success State**: Focuses exclusively on genuine high-severity incidents and proactive hunting

### Tertiary Persona: CISO / Security Manager — "Priya"

- **Role**: Head of security, reports to CTO
- **Daily Task**: Weekly threat summary, compliance review, team performance oversight
- **Pain Points**: No visibility into SOC throughput or analyst efficiency; manual weekly reporting
- **Goals**: Dashboard with KPIs; exportable reports; confidence that critical threats are never missed
- **Technical Proficiency**: Low-to-medium — needs UI, not CLI
- **Success State**: Weekly threat summary auto-generated; real-time KPI visibility

---

## 5. Features & Requirements

### Must-Have Features (P0)

**1. Multi-Source Log Ingestion**
- Description: Accept log events from syslog, JSON-over-HTTP, and file upload; normalize to a common schema
- User Story: As a security engineer, I want to connect my existing log sources so that I don't have to change my logging infrastructure
- Acceptance Criteria:
  - [ ] Accepts syslog (RFC 5424), JSON HTTP POST, and CSV file upload
  - [ ] Normalizes all inputs to common event schema (timestamp, source_ip, dest_ip, event_type, raw_payload)
  - [ ] Handles ≥ 10,000 events/minute without data loss
  - [ ] Displays ingestion health status per source
- Success Metric: All configured sources show "healthy" status; zero events dropped under normal load

**2. AI Anomaly Detection**
- Description: Run Isolation Forest + behavioral baseline models on the event stream to identify statistical outliers
- User Story: As a Tier 1 analyst, I want the system to automatically flag unusual events so that I don't have to manually review all 10,000 events per minute
- Acceptance Criteria:
  - [ ] Isolation Forest model scores every event with an anomaly score (0.0–1.0)
  - [ ] Behavioral baseline established after 72 hours of training data
  - [ ] Alerts generated for events with score > configurable threshold (default: 0.75)
  - [ ] Model retrains weekly on analyst feedback data
- Success Metric: < 30% false positive rate on high-confidence alerts (score > 0.85)

**3. LLM Threat Explanation Engine**
- Description: For every generated alert, call Claude API with alert context + RAG-retrieved threat intel to produce a plain-language explanation
- User Story: As a Tier 1 analyst, I want to see a plain-English explanation of what the threat is and why it's suspicious so that I can make a triage decision in under 30 seconds
- Acceptance Criteria:
  - [ ] Every alert has an explanation ≤ 150 words covering: what happened, why suspicious, recommended action
  - [ ] Explanation generated within 10 seconds of alert creation
  - [ ] Explanation cached — identical alert patterns reuse cached explanation
  - [ ] Analyst can rate explanation as helpful / not helpful
- Success Metric: ≥ 90% of explanations rated "helpful" by analysts

**4. MITRE ATT&CK Mapping**
- Description: Map each alert to the most likely MITRE ATT&CK tactic and technique using RAG over the ATT&CK knowledge base
- User Story: As a Tier 2 analyst, I want every alert tagged with its MITRE tactic so that I can understand the threat in context of the kill chain
- Acceptance Criteria:
  - [ ] Every alert tagged with at least one MITRE tactic (e.g., Lateral Movement, Exfiltration)
  - [ ] Technique ID shown (e.g., T1071.001)
  - [ ] Confidence score for mapping shown
  - [ ] Clickable link to MITRE ATT&CK page
- Success Metric: Tier 2 analyst agrees with MITRE mapping ≥ 85% of the time

**5. Alert Dashboard**
- Description: Real-time dashboard showing all active alerts, sortable and filterable by severity, source, time, and MITRE tactic
- User Story: As a Tier 1 analyst, I want a single pane of glass for all active alerts so that I can prioritize my triage queue
- Acceptance Criteria:
  - [ ] Displays all open alerts with severity badge (critical/high/medium/low)
  - [ ] Updates in real time (< 5 second refresh)
  - [ ] Filterable by: severity, source, time range, MITRE tactic, status
  - [ ] Each row shows: timestamp, source IP, event type, severity, MITRE tactic, status
  - [ ] Click-through to full alert detail view
- Success Metric: Dashboard loads in < 2 seconds; alert updates appear within 5 seconds

**6. Alert Detail View**
- Description: Full detail page for a single alert with AI explanation, raw event data, timeline, and analyst action buttons
- User Story: As a Tier 1 analyst, I want to see everything relevant about an alert in one view so that I can triage without switching tools
- Acceptance Criteria:
  - [ ] Shows AI explanation, MITRE mapping, severity score, source IP geolocation
  - [ ] Shows raw event payload
  - [ ] Shows timeline of related events from same source IP (last 24 hours)
  - [ ] Action buttons: Escalate, Dismiss, Mark as False Positive, Add Note
  - [ ] Notes visible to all analysts
- Success Metric: Analyst completes triage action within 60 seconds of opening detail view

**7. Severity Scoring & Correlation**
- Description: Combine anomaly score, threat intel matches, MITRE tactic severity, and asset criticality to produce a final severity rating
- User Story: As an analyst, I want alerts ranked by true risk so that I work on the most dangerous threats first
- Acceptance Criteria:
  - [ ] Severity = weighted formula: anomaly_score × 0.4 + intel_match × 0.3 + tactic_weight × 0.2 + asset_criticality × 0.1
  - [ ] Four tiers: Critical (≥ 0.85), High (0.65–0.84), Medium (0.40–0.64), Low (< 0.40)
  - [ ] Scoring is transparent — analyst can see score breakdown
- Success Metric: Tier 2 analysts agree with severity assignment ≥ 80% of the time

### Should-Have Features (P1)

**8. Analyst Feedback & Model Retraining Loop**
- False positive dismissals feed back into the model weekly
- Analyst ratings of explanations used to tune prompt quality

**9. Search & Historical Query**
- Full-text search across alerts and raw events
- Date range queries with export to CSV

**10. Data Source Management UI**
- Web UI to add/remove/configure log sources
- Per-source ingestion health metrics

**11. Basic Reporting**
- Weekly automated summary: alert volume, severity breakdown, top sources, top MITRE tactics
- Exportable as PDF

### Nice-to-Have Features (P2)

**12. SOAR Playbook Triggers** — Webhook out to PagerDuty / Slack on critical alerts  
**13. Custom Detection Rules** — Analyst-defined Sigma rules layered on top of ML  
**14. Network Traffic Analysis** — PCAP ingestion + flow analysis  
**15. Asset Inventory Integration** — Pull asset criticality from CMDB  
**16. Mobile App** — Read-only alert monitoring on iOS/Android  

---

## 6. Explicitly OUT OF SCOPE (MVP)

- Full SOAR automation (auto-blocking IPs, auto-isolating hosts) — too high-risk without more validation
- Compliance report generation (SOC 2, ISO 27001) — separate product track
- Threat hunting workbench — Phase 2
- EDR / endpoint agent deployment — relies on third-party EDR
- Mobile application
- Multi-tenant SaaS mode — single-org deployment only at MVP
- Vulnerability scanner integration
- Dark web monitoring
- Deception / honeypot management
- User and Entity Behavior Analytics (UEBA) beyond basic anomaly detection

---

## 7. User Scenarios

### Scenario 1: Analyst triages a high-severity alert

- **Context**: Tuesday 2 AM, Tier 1 analyst on overnight shift, receives a critical alert
- **Steps**:
  1. Alert appears at top of dashboard: "Critical — Unusual outbound traffic — 10.0.1.44 → 185.220.101.45 — Exfiltration?"
  2. Analyst clicks alert; detail view loads in < 2 seconds
  3. AI explanation reads: "Host 10.0.1.44 (Finance-Workstation-07) sent 2.3 GB to IP 185.220.101.45 (Tor exit node, Romania) over port 443 in a 4-minute window — 47× above baseline for this host. This pattern matches T1048 (Exfiltration Over Alternative Protocol). Recommended action: isolate host and capture full packet data for forensics."
  4. Analyst clicks "Escalate" and adds note: "Possible data exfiltration, isolating host per procedure"
  5. Tier 2 analyst paged automatically
- **Expected Outcome**: Escalation logged with full context; Tier 2 has everything needed without re-investigation
- **Edge Cases**: Host is offline when analyst tries to verify; multiple alerts from same host in last hour

### Scenario 2: Analyst dismisses a false positive

- **Context**: Routine backup job triggers anomaly detection
- **Steps**:
  1. Medium-severity alert: "Unusual data transfer — Backup-Server-01 → 10.0.5.100"
  2. AI explanation: "Backup-Server-01 transferred 180 GB to 10.0.5.100 between 01:00–03:00. While volume is above daily baseline, destination is an internal storage server. Pattern is consistent with scheduled backup behavior."
  3. Analyst marks as "False Positive" with note: "Scheduled weekly backup, confirmed with IT"
  4. System records feedback for model retraining
- **Expected Outcome**: Alert dismissed in < 15 seconds; feedback recorded
- **Edge Cases**: Analyst dismisses without adding a note (system prompts but doesn't require)

### Scenario 3: CISO reviews weekly summary

- **Context**: Friday morning, CISO wants a summary before board meeting
- **Steps**:
  1. CISO logs into dashboard, navigates to Reports
  2. Selects "Weekly Summary — May 19–26"
  3. Report shows: 1,247 alerts, 3 critical (all escalated), 18% false positive rate, top tactic: Initial Access (34%), mean triage time: 18 minutes
  4. Exports as PDF
- **Expected Outcome**: Report generated in < 10 seconds; PDF matches screen data
- **Edge Cases**: Report period spans a system downtime window (shown as data gap, not zero)

---

## 8. Non-Functional Requirements

- **Performance**: Ingest ≥ 10,000 events/minute; dashboard loads < 2s; alert explanation generated < 10s
- **Security**: All API endpoints require JWT auth; all data encrypted at rest (AES-256) and in transit (TLS 1.3); no raw passwords stored; SOC 2 Type I ready architecture
- **Availability**: 99.5% uptime target; alert pipeline continues even if dashboard is down
- **Scalability**: Horizontal scaling of ingestion workers; database partitioned by time
- **Accessibility**: WCAG 2.1 Level AA; dashboard usable at 1280×720 minimum resolution
- **Data Retention**: Raw events retained 90 days; alerts retained 1 year; analyst notes retained indefinitely

---

## 9. Dependencies & Constraints

- **Anthropic API**: LLM explanation engine depends on Claude API availability; fallback is explanation-pending state (alert still shown)
- **MITRE ATT&CK**: ATT&CK knowledge base embedded via RAG; updated quarterly
- **Budget**: API costs for LLM calls must stay under $500/month at 10,000 alerts/day (achieved via caching)
- **Team**: 2 backend engineers, 1 frontend engineer, 1 ML engineer for MVP build
- **Timeline**: MVP in 8 weeks

---

## 10. Timeline & Milestones

| Milestone | Target Date | Features Included |
|-----------|-------------|-------------------|
| M1: Foundation | Week 2 | Ingestion pipeline, DB schema, basic API |
| M2: Detection | Week 4 | Anomaly detection, alert generation, severity scoring |
| M3: Intelligence | Week 6 | LLM explanations, MITRE RAG, dashboard MVP |
| M4: MVP Launch | Week 8 | All P0 features, analyst feedback loop, staging deploy |
| M5: P1 Features | Week 14 | Search, reporting, data source management UI |

---

## 11. Risks & Assumptions

### Risks

- **LLM hallucination in threat explanations**: Mitigated by grounding every explanation in RAG-retrieved facts and requiring the model to cite the specific event data
- **High false positive rate degrading analyst trust**: Mitigated by tunable thresholds and rapid feedback loop
- **API cost overrun**: Mitigated by aggressive caching — identical alert signatures reuse cached explanations
- **Data volume exceeding infrastructure**: Mitigated by Kafka backpressure and horizontal worker scaling

### Assumptions

- Organizations have existing log sources they can forward (syslog or JSON)
- Analysts have basic cybersecurity training — this tool assists, not replaces, human judgment
- 72 hours of baseline traffic is sufficient for initial anomaly model (assumption to validate post-launch)
- Anthropic API maintains current pricing and availability
