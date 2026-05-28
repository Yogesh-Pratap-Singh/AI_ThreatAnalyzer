from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
import uuid

# --- Authentication Schemas ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str

    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    user: UserResponse

# --- Ingestion Schemas ---
class EventIngestSchema(BaseModel):
    timestamp: datetime
    source_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    source_port: Optional[int] = None
    dest_port: Optional[int] = None
    protocol: Optional[str] = None
    event_type: str
    bytes: Optional[int] = None
    raw: Dict[str, Any] = {}

class IngestRequest(BaseModel):
    source_id: uuid.UUID
    events: List[EventIngestSchema]

# --- Alert Schemas ---
class AlertResponse(BaseModel):
    id: uuid.UUID
    title: str
    severity: str
    severity_score: float
    source_ip: Optional[str]
    dest_ip: Optional[str]
    event_type: str
    mitre_tactic: Optional[str]
    mitre_technique_id: Optional[str]
    status: str
    event_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class PaginationMetadata(BaseModel):
    page: int
    limit: int
    total: int
    pages: int

class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    pagination: PaginationMetadata

class SeverityBreakdown(BaseModel):
    anomaly_score: float
    intel_match_score: float
    tactic_weight: float
    asset_criticality: float

class NoteUser(BaseModel):
    id: uuid.UUID
    full_name: str

class NoteResponse(BaseModel):
    id: uuid.UUID
    alert_id: uuid.UUID
    user: Optional[NoteUser]
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class RelatedEventResponse(BaseModel):
    id: uuid.UUID
    event_time: datetime
    event_type: str
    bytes_transferred: Optional[int]
    anomaly_score: float

    class Config:
        from_attributes = True

class AlertDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    severity: str
    severity_score: float
    severity_breakdown: SeverityBreakdown
    source_ip: Optional[str]
    dest_ip: Optional[str]
    source_port: Optional[int]
    dest_port: Optional[int]
    event_type: str
    bytes_transferred: Optional[int]
    mitre_tactic: Optional[str]
    mitre_technique_id: Optional[str]
    mitre_technique_name: Optional[str] = None
    mitre_confidence: Optional[float]
    mitre_url: Optional[str] = None
    status: str
    event_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    notes: List[NoteResponse] = []
    explanation: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AlertDetailContainer(BaseModel):
    alert: AlertDetailResponse
    related_events: List[RelatedEventResponse]

class AlertActionRequest(BaseModel):
    action: str  # escalate, dismiss, false_positive, resolve
    priority: Optional[str] = None  # P1, P2, P3
    assignee_id: Optional[uuid.UUID] = None
    note: Optional[str] = None

class NoteRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)

# --- Feedback Schemas ---
class FeedbackRequest(BaseModel):
    alert_id: uuid.UUID
    feedback_type: str  # false_positive, explanation_helpful, explanation_not_helpful
    fp_reason: Optional[str] = None  # scheduled_job, known_safe, misconfiguration, other
    notes: Optional[str] = None

# --- Report Schemas ---
class PeriodSummary(BaseModel):
    from_time: datetime = Field(..., alias="from")
    to_time: datetime = Field(..., alias="to")

class TacticCount(BaseModel):
    tactic: str
    count: int

class SourceIpCount(BaseModel):
    ip: str
    alert_count: int

class DailyVolume(BaseModel):
    date: str
    count: int

class ReportResponse(BaseModel):
    period: PeriodSummary
    total_alerts: int
    by_severity: Dict[str, int]
    false_positive_rate: float
    mean_triage_time_minutes: int
    top_mitre_tactics: List[TacticCount]
    top_source_ips: List[SourceIpCount]
    alert_volume_by_day: List[DailyVolume]
