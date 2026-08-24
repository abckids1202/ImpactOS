from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now() -> datetime:
    return datetime.utcnow()


class School(Base):
    __tablename__ = "schools"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    mode: Mapped[str] = mapped_column(String(30), default="DEMO")
    language: Mapped[str] = mapped_column(String(20), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(30), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class SchoolSetting(Base):
    __tablename__ = "school_settings"
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), primary_key=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ProblemReport(Base):
    __tablename__ = "problem_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    affected_group: Mapped[str] = mapped_column(String(160), default="")
    scope: Mapped[str] = mapped_column(String(120), default="")
    category: Mapped[str] = mapped_column(String(80), default="OTHER")
    frequency: Mapped[str] = mapped_column(String(80), default="")
    severity: Mapped[str] = mapped_column(String(40), default="MEDIUM")
    visibility: Mapped[str] = mapped_column(String(40), default="SCHOOL_NAMED")
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", index=True)
    sensitivity_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cluster_id: Mapped[Optional[str]] = mapped_column(ForeignKey("problem_clusters.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ProblemCluster(Base):
    __tablename__ = "problem_clusters"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    summary: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), default="OTHER")
    scope: Mapped[str] = mapped_column(String(120), default="School")
    status: Mapped[str] = mapped_column(String(40), default="NEW", index=True)
    priority_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ProblemSignal(Base):
    __tablename__ = "problem_signals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cluster_id: Mapped[str] = mapped_column(ForeignKey("problem_clusters.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    __table_args__ = (UniqueConstraint("cluster_id", "user_id", "signal_type", name="uq_signal_once"),)


class Evidence(Base):
    __tablename__ = "evidence_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    cluster_id: Mapped[Optional[str]] = mapped_column(ForeignKey("problem_clusters.id"), nullable=True, index=True)
    research_id: Mapped[Optional[str]] = mapped_column(ForeignKey("research_projects.id"), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(ForeignKey("impact_projects.id"), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(160))
    evidence_type: Mapped[str] = mapped_column(String(60), default="OBSERVATION")
    observation_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    relevance: Mapped[str] = mapped_column(Text, default="")
    visibility: Mapped[str] = mapped_column(String(40), default="TEAM")
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class StatusEvent(Base):
    __tablename__ = "status_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    from_status: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    to_status: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text, default="")
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class OfficialUpdate(Base):
    __tablename__ = "official_updates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    cluster_id: Mapped[str] = mapped_column(ForeignKey("problem_clusters.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ResearchProject(Base):
    __tablename__ = "research_projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    cluster_id: Mapped[str] = mapped_column(ForeignKey("problem_clusters.id"), index=True)
    leader_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", index=True)
    mentor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ResearchPlanVersion(Base):
    __tablename__ = "research_plan_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    research_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    immutable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(40))
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Survey(Base):
    __tablename__ = "surveys"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    research_id: Mapped[str] = mapped_column(ForeignKey("research_projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    purpose: Mapped[str] = mapped_column(Text, default="")
    privacy_mode: Mapped[str] = mapped_column(String(30), default="ANONYMOUS")
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    one_response: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class SurveyQuestion(Base):
    __tablename__ = "survey_questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    survey_id: Mapped[str] = mapped_column(ForeignKey("surveys.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    question_type: Mapped[str] = mapped_column(String(30))
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSON, default=list)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("survey_id", "position", name="uq_question_position"),)


class SurveyResponse(Base):
    __tablename__ = "survey_responses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    survey_id: Mapped[str] = mapped_column(ForeignKey("surveys.id"), index=True)
    respondent_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), unique=True)
    answers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ImpactProject(Base):
    __tablename__ = "impact_projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    research_id: Mapped[Optional[str]] = mapped_column(ForeignKey("research_projects.id"), nullable=True, index=True)
    cluster_id: Mapped[str] = mapped_column(ForeignKey("problem_clusters.id"), index=True)
    leader_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    target_users: Mapped[str] = mapped_column(Text, default="")
    intervention: Mapped[str] = mapped_column(Text, default="")
    theory_of_change: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    resources: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="DRAFT", index=True)
    mentor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ProjectTask(Base):
    __tablename__ = "project_tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("impact_projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    owner_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="TODO")
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    due_date: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)


class Metric(Base):
    __tablename__ = "impact_metrics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("impact_projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str] = mapped_column(String(80))
    direction: Mapped[str] = mapped_column(String(30), default="DECREASE")
    collection_method: Mapped[str] = mapped_column(Text, default="")
    target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Observation(Base):
    __tablename__ = "metric_observations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    metric_id: Mapped[str] = mapped_column(ForeignKey("impact_metrics.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("impact_projects.id"), index=True)
    phase: Mapped[str] = mapped_column(String(20))
    value: Mapped[float] = mapped_column(Float)
    observed_on: Mapped[str] = mapped_column(String(30))
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    recorder_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ImpactReport(Base):
    __tablename__ = "impact_report_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("impact_projects.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    immutable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    metadata_safe: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)


class Invitation(Base):
    __tablename__ = "invitations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str] = mapped_column(String(30), default="STUDENT")
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class PublicImpactStory(Base):
    __tablename__ = "public_impact_stories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    source_project_id: Mapped[Optional[str]] = mapped_column(ForeignKey("impact_projects.id"), nullable=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    problem_summary: Mapped[str] = mapped_column(Text)
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    research_question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    intervention_summary: Mapped[str] = mapped_column(Text)
    measurement_summary: Mapped[str] = mapped_column(Text)
    observed_result: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str] = mapped_column(Text)
    what_did_not_work: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    official_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    result_type: Mapped[str] = mapped_column(String(30), default="INCONCLUSIVE")
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    public_team_label: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    published_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
