import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Table, Column, ForeignKey, String, Boolean, DateTime, Float, BigInteger, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base

# Junction table for Alerts and Events
alert_events = Table(
    "alert_events",
    Base.metadata,
    Column("alert_id", UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("event_id", UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="analyst", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    actioned_alerts: Mapped[List["Alert"]] = relationship("Alert", foreign_keys="[Alert.actioned_by]", back_populates="actioned_by_user")
    escalated_alerts: Mapped[List["Alert"]] = relationship("Alert", foreign_keys="[Alert.escalated_to]", back_populates="escalated_to_user")

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")

class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # syslog, json_http, csv_upload
    config_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True, nullable=False)  # active, degraded, disconnected
    last_event_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    events_per_minute: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    events: Mapped[List["Event"]] = relationship("Event", back_populates="source", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    dest_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    source_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dest_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    bytes_transferred: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    source: Mapped["DataSource"] = relationship("DataSource", back_populates="events")
    alerts: Mapped[List["Alert"]] = relationship("Alert", secondary=alert_events, back_populates="events")

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # critical, high, medium, low
    severity_score: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    intel_match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tactic_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    asset_criticality: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    dest_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    mitre_tactic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    mitre_technique_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mitre_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    alert_signature: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)  # open, escalated, dismissed, false_positive, resolved
    event_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actioned_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_to: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    actioned_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actioned_by], back_populates="actioned_alerts")
    escalated_to_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[escalated_to], back_populates="escalated_alerts")
    events: Mapped[List["Event"]] = relationship("Event", secondary=alert_events, back_populates="alerts")
    notes: Mapped[List["AnalystNote"]] = relationship("AnalystNote", back_populates="alert", cascade="all, delete-orphan")
    feedbacks: Mapped[List["AnalystFeedback"]] = relationship("AnalystFeedback", back_populates="alert", cascade="all, delete-orphan")

class ThreatExplanation(Base):
    __tablename__ = "threat_explanations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_signature: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    explanation_text: Mapped[str] = mapped_column(String, nullable=False)
    mitre_tactic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mitre_technique_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    not_helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class AnalystNote(Base):
    __tablename__ = "analyst_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="notes")
    user: Mapped[Optional["User"]] = relationship("User")

class AnalystFeedback(Base):
    __tablename__ = "analyst_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(30), nullable=False)  # false_positive, explanation_helpful, explanation_not_helpful
    fp_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # scheduled_job, known_safe, misconfiguration, other
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    alert_signature: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="feedbacks")
    user: Mapped[Optional["User"]] = relationship("User")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # mitre_attack, cve, threat_report
    source_id: Mapped[str] = mapped_column(String(50), nullable=False)  # T1048.001, CVE-2024-1234
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(JSON, nullable=False)  # Fallback to JSON array for floats
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
