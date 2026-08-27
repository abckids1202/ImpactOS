from __future__ import annotations

import csv
import io
import os
import re
import secrets
import time
from collections import defaultdict, deque
from threading import Lock
from datetime import date, datetime, timedelta
from statistics import mean, median
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import SessionLocal, get_db, init_db
from .models import (
    AuditLog,
    AuthSession,
    Evidence,
    Feedback,
    ImpactProject,
    ImpactReport,
    Metric,
    Notification,
    Observation,
    OfficialUpdate,
    ProblemCluster,
    ProblemFollow,
    ProblemPriority,
    ProblemReport,
    ProblemSignal,
    PublicImpactStory,
    ProjectTask,
    ResponseCommitment,
    ResponseCommitmentUpdate,
    Invitation,
    InvitationRole,
    Membership,
    PasswordResetToken,
    ResearchPlanVersion,
    ResearchProject,
    Role,
    RoleAssignment,
    Review,
    School,
    SchoolSetting,
    StatusEvent,
    Survey,
    SurveyQuestion,
    SurveyResponse,
    User,
)
from .schemas import (
    DecisionRequest,
    EvidenceCreate,
    FeedbackCreate,
    ImpactCreate,
    ImpactUpdate,
    InvitationAccept,
    InvitationCreate,
    LoginRequest,
    MergeRequest,
    MetricCreate,
    ObservationCreate,
    OfficialUpdateCreate,
    ProblemCreate,
    ProblemUpdate,
    ResearchCreate,
    ResearchPlanUpdate,
    ReportUpdate,
    SignalCreate,
    ActivationEmailRequest,
    AuthMeResponse,
    PasswordForgotRequest,
    PasswordResetRequest,
    PriorityRequest,
    PriorityAssessmentRequest,
    ResponseCommitmentComplete,
    ResponseCommitmentCreate,
    ResponseCommitmentPatch,
    ResponseCommitmentTransfer,
    ResponseCommitmentUpdateCreate,
    RoleAssignmentRequest,
    SurveyCreate,
    SurveyQuestionCreate,
    SurveyResponseCreate,
    TaskUpdate,
    UserRead,
)
from .security import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    active_permissions,
    active_role_codes,
    create_session,
    get_current_user,
    hash_password,
    normalize_role,
    password_needs_upgrade,
    require_csrf,
    require_permissions,
    require_roles,
    revoke_all_sessions,
    revoke_session,
    session_cookie_options,
    token_hash as secure_token_hash,
    validate_security_config,
    verify_password,
)


app = FastAPI(title="ImpactOS API", version="0.1.0", description="Pilar Impact Lab closed-alpha API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = f"req_{uuid4().hex}"
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


def _error_payload(request: Request, code: str, message: str, field_errors: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "field_errors": field_errors or {}, "request_id": getattr(request.state, "request_id", f"req_{uuid4().hex}")}}


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    code = str(detail.get("code", "INTERNAL_ERROR" if exc.status_code >= 500 else "REQUEST_FAILED"))
    message = str(detail.get("message", exc.detail if isinstance(exc.detail, str) else "The request could not be completed."))
    return JSONResponse(status_code=exc.status_code, content={**_error_payload(request, code, message, detail.get("field_errors")), "detail": exc.detail}, headers={"X-Request-ID": getattr(request.state, "request_id", "")})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    field_errors = {".".join(str(part) for part in error.get("loc", [])[1:]): error.get("msg", "Invalid value") for error in exc.errors()}
    payload = _error_payload(request, "VALIDATION_ERROR", "Please correct the highlighted fields.", field_errors)
    return JSONResponse(status_code=422, content={**payload, "detail": payload["error"]}, headers={"X-Request-ID": getattr(request.state, "request_id", "")})

API = "/api/v1"
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo1234")
_RATE_LIMITS: dict[str, deque[float]] = defaultdict(deque)
_RATE_LIMIT_LOCK = Lock()


def enforce_rate_limit(request: Request, bucket: str, limit: int = 8, window_seconds: int = 300) -> None:
    key = f"{bucket}:{request.client.host if request.client else 'unknown'}"
    now = time.monotonic()
    with _RATE_LIMIT_LOCK:
        events = _RATE_LIMITS[key]
        while events and now - events[0] > window_seconds:
            events.popleft()
        if len(events) >= limit:
            raise HTTPException(status_code=429, detail={"code": "RATE_LIMITED", "message": "Too many attempts. Please wait and try again."})
        events.append(now)


def app_mode() -> str:
    return os.getenv("APP_MODE", "DEMO").upper()


def demo_access_allowed() -> bool:
    return app_mode() == "DEMO" and os.getenv("ENVIRONMENT", "development").lower() not in {"production", "prod"}


PUBLIC_FAQ = [
    {"category": "About the platform", "question": "What is Pilar Impact Lab?", "answer": "Pilar Impact Lab is SPI's structured path for turning student observations into evidence-backed projects and measured learning. It is powered by ImpactOS."},
    {"category": "Membership", "question": "Who can use the internal platform?", "answer": "Approved SPI members and invited project participants. Privileged roles are assigned by authorized staff; there is no unrestricted public registration."},
    {"category": "Privacy", "question": "Can anyone see student problem reports?", "answer": "No. Public pages contain only approved, sanitized impact stories. Internal reports, identities, survey responses, evidence, and moderation records remain restricted."},
    {"category": "AI", "question": "Does AI make school decisions?", "answer": "No. AI may suggest clarification or methodology help. People decide visibility, approvals, moderation, publication, and school policy."},
    {"category": "Privacy", "question": "What happens when a report is sensitive?", "answer": "It is routed to restricted review and does not appear in the public problem space. ImpactOS is not an emergency reporting service."},
    {"category": "Public impact stories", "question": "Can a project publish a negative result?", "answer": "Yes. Approved stories may explain positive, negative, mixed, or inconclusive observed results and their limitations."},
]


def public_story_dict(story: PublicImpactStory) -> dict[str, Any]:
    # This allowlist intentionally excludes school_id, source_project_id, user IDs,
    # internal UUIDs, audit history, and every raw internal artifact.
    return {
        "slug": story.slug,
        "title": story.title,
        "problem_summary": story.problem_summary,
        "evidence_summary": story.evidence_summary,
        "research_question": story.research_question,
        "intervention_summary": story.intervention_summary,
        "measurement_summary": story.measurement_summary,
        "observed_result": story.observed_result,
        "limitations": story.limitations,
        "what_did_not_work": story.what_did_not_work,
        "next_steps": story.next_steps,
        "official_response": story.official_response,
        "category": story.category,
        "result_type": story.result_type,
        "status": story.status,
        "public_team_label": story.public_team_label,
        "is_synthetic": story.is_synthetic,
        "published_at": dt(story.published_at),
    }


def new_id() -> str:
    return str(uuid4())


def dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def user_dict(user: User) -> dict[str, Any]:
    return UserRead.model_validate(user).model_dump()


ROLE_DETAILS = {
    "STUDENT_CONTRIBUTOR": ("Student contributor", "Reports concerns and contributes evidence."),
    "STUDENT_PROJECT_LEADER": ("Student project leader", "Leads approved research and intervention work."),
    "MENTOR": ("Mentor", "Reviews student plans and decisions."),
    "OSIS_REVIEWER": ("OSIS reviewer", "Reviews non-sensitive school-wide priorities."),
    "MODERATOR": ("Moderator", "Reviews reports, safety, visibility, and merging."),
    "ADMINISTRATOR": ("Administrator", "Manages users, roles, configuration, and audit records."),
}


def ensure_identity_records(db: Session, user: User, role_codes: list[str] | None = None, assigned_by: str | None = None) -> Membership:
    membership = db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.school_id == user.school_id))
    if not membership:
        membership = Membership(id=new_id(), user_id=user.id, school_id=user.school_id, status="ACTIVE")
        db.add(membership)
        db.flush()
    codes = role_codes or [normalize_role(user.role)]
    for code in codes:
        canonical = normalize_role(code)
        role = db.scalar(select(Role).where(Role.code == canonical))
        if not role:
            name, description = ROLE_DETAILS.get(canonical, (canonical.replace("_", " ").title(), ""))
            role = Role(id=new_id(), code=canonical, name=name, description=description)
            db.add(role)
            db.flush()
        assignment = db.scalar(select(RoleAssignment).where(RoleAssignment.membership_id == membership.id, RoleAssignment.role_id == role.id))
        if not assignment:
            db.add(RoleAssignment(id=new_id(), membership_id=membership.id, role_id=role.id, assigned_by=assigned_by))
        elif assignment.revoked_at:
            assignment.revoked_at = None
    return membership


def auth_me_dict(db: Session, user: User) -> dict[str, Any]:
    membership = ensure_identity_records(db, user)
    school = db.get(School, user.school_id)
    roles = active_role_codes(db, user)
    return {
        "user": {"id": user.id, "email": user.email, "display_name": user.display_name, "status": getattr(user, "status", "ACTIVE")},
        "memberships": [{
            "id": membership.id,
            "school": {"id": school.id if school else user.school_id, "name": school.name if school else "Sekolah Pilar Indonesia", "slug": school.slug if school else "pilar-impact-lab"},
            "roles": roles,
            "permissions": active_permissions(db, user),
            "status": membership.status,
        }],
    }


def audit(db: Session, actor: User | None, action: str, entity_type: str, entity_id: str | None, metadata: dict[str, Any] | None = None, request: Request | None = None, school_id: str | None = None) -> None:
    db.add(
        AuditLog(
            id=new_id(),
            school_id=actor.school_id if actor else (school_id or "school-pilar"),
            actor_id=actor.id if actor else None,
            actor_user_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_safe=metadata or {},
            request_id=getattr(request.state, "request_id", None) if request else None,
        )
    )


def notify(db: Session, user_id: str | None, title: str, message: str) -> None:
    if user_id:
        db.add(Notification(id=new_id(), user_id=user_id, title=title, message=message))


RESPONSE_COMMITMENT_TRANSITIONS = {
    "OPEN": {"IN_PROGRESS", "BLOCKED", "COMPLETED", "DECLINED", "NOT_NOW"},
    "IN_PROGRESS": {"OPEN", "BLOCKED", "COMPLETED", "DECLINED", "NOT_NOW"},
    "BLOCKED": {"OPEN", "IN_PROGRESS", "COMPLETED", "DECLINED", "NOT_NOW"},
    "NOT_NOW": {"OPEN", "IN_PROGRESS", "COMPLETED"},
    "DECLINED": {"OPEN", "IN_PROGRESS"},
    "COMPLETED": set(),
}
RESPONSE_COMMITMENT_TERMINAL = {"COMPLETED", "DECLINED"}
RESPONSE_VISIBLE_CLUSTER_STATES = {"VALIDATED", "UNDER_INVESTIGATION", "ACTION_PLANNED", "ACTION_UNDERWAY", "RESOLVED", "IMPACT_MEASURED", "CLOSED"}


def parse_day(value: str | None, field_name: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} must use YYYY-MM-DD format.") from exc


def school_days_between(start: date, end: date) -> int:
    """Return weekday count from start up to end, excluding the end date."""
    if end <= start:
        return 0
    current = start
    count = 0
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return count


def commitment_reminder(item: ResponseCommitment) -> tuple[str, str] | None:
    if item.status in RESPONSE_COMMITMENT_TERMINAL:
        return None
    today = date.today()
    due = parse_day(item.due_date, "due_date")
    update_due = parse_day(item.next_update_date, "next_update_date")
    candidates = [(due, "Action due") if due else None, (update_due, "Status update due") if update_due else None]
    candidates = [candidate for candidate in candidates if candidate]
    if not candidates:
        return None
    target, label = min(candidates, key=lambda candidate: candidate[0])
    if target < today:
        if school_days_between(target, today) < 3:
            return None
        return "OVERDUE", f"{label} for {item.title} was due on {target.isoformat()}. Add an update or revise the commitment."
    if target == today:
        return "DUE_TODAY", f"{label} for {item.title} is due today."
    if school_days_between(today, target) <= 3:
        return "DUE_SOON", f"{label} for {item.title} is due on {target.isoformat()}."
    return None


def commitment_scope(db: Session, actor: User, item: ResponseCommitment) -> tuple[bool, bool]:
    manager = has_active_role(db, actor, "MENTOR", "OSIS", "ADMIN")
    return actor.id == item.owner_id or manager, manager


def validate_commitment_links(db: Session, actor: User, cluster_id: str, research_id: str | None, project_id: str | None) -> None:
    if research_id:
        research = db.get(ResearchProject, research_id)
        if not research or research.school_id != actor.school_id or research.cluster_id != cluster_id:
            raise HTTPException(status_code=404, detail="Linked research workspace not found.")
    if project_id:
        project = db.get(ImpactProject, project_id)
        if not project or project.school_id != actor.school_id or project.cluster_id != cluster_id:
            raise HTTPException(status_code=404, detail="Linked impact project not found.")


def validate_commitment_owner(db: Session, actor: User, owner_role: str, owner_id: str | None) -> tuple[str, User | None]:
    role = owner_role.strip().upper().replace(" ", "_")
    role = normalize_role(role)
    owner = None
    if owner_id:
        owner = db.get(User, owner_id)
        if not owner or owner.school_id != actor.school_id or not owner.active or getattr(owner, "status", "ACTIVE") != "ACTIVE":
            raise HTTPException(status_code=404, detail="Commitment owner not found.")
        if role in ROLE_DETAILS and role not in active_role_codes(db, owner):
            raise HTTPException(status_code=422, detail="The selected owner does not hold the accountable role.")
    return role, owner


def commitment_dict(db: Session, item: ResponseCommitment, actor: User, include_updates: bool = True) -> dict[str, Any]:
    owner = db.get(User, item.owner_id) if item.owner_id else None
    can_manage, manager = commitment_scope(db, actor, item)
    reminder = commitment_reminder(item)
    updates = db.scalars(select(ResponseCommitmentUpdate).where(ResponseCommitmentUpdate.commitment_id == item.id).order_by(ResponseCommitmentUpdate.created_at.desc()).limit(8)).all() if include_updates else []
    visible_updates = [update for update in updates if update.visibility == "SCHOOL" or can_manage]
    cluster = db.get(ProblemCluster, item.cluster_id)
    return {
        "id": item.id,
        "type": "RESPONSE_COMMITMENT",
        "title": item.title,
        "intended_outcome": item.intended_outcome,
        "cluster_id": item.cluster_id,
        "cluster_title": cluster.title if cluster else None,
        "research_id": item.research_id,
        "project_id": item.project_id,
        "owner_role": item.owner_role,
        "owner_id": item.owner_id,
        "owner_name": owner.display_name if owner else None,
        "status": item.status,
        "priority": item.priority,
        "due_date": item.due_date,
        "next_update_date": item.next_update_date,
        "blocker": item.blocker if can_manage else "",
        "completion_note": item.completion_note if can_manage else "",
        "evidence_reference": item.evidence_reference if can_manage else "",
        "visibility": item.visibility,
        "is_overdue": bool(reminder and reminder[0] == "OVERDUE") if (can_manage or manager) else False,
        "is_stale": bool(reminder and reminder[0] == "OVERDUE") if (can_manage or manager) else False,
        "reminder_state": reminder[0] if reminder and (can_manage or manager) else None,
        "reminder_message": reminder[1] if reminder and (can_manage or manager) else None,
        "updates": [{"id": update.id, "kind": update.kind, "message": update.message, "visibility": update.visibility, "created_at": dt(update.created_at)} for update in visible_updates],
        "href": f"/app/problems/{item.cluster_id}",
        "created_at": dt(item.created_at),
        "updated_at": dt(item.updated_at),
    }


def cluster_timeline(db: Session, cluster: ProblemCluster, actor: User) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    status_events = db.scalars(select(StatusEvent).where(StatusEvent.entity_type == "PROBLEM_CLUSTER", StatusEvent.entity_id == cluster.id).order_by(StatusEvent.created_at.desc()).limit(40)).all()
    for event in status_events:
        events.append({"id": event.id, "type": "STATUS", "title": f"Problem moved to {event.to_status.replace('_', ' ').title()}", "message": event.reason or "Workflow status updated.", "status": event.to_status, "created_at": dt(event.created_at)})
    official_updates = db.scalars(select(OfficialUpdate).where(OfficialUpdate.cluster_id == cluster.id, OfficialUpdate.status == "PUBLISHED").order_by(OfficialUpdate.created_at.desc()).limit(30)).all()
    for update in official_updates:
        events.append({"id": update.id, "type": "OFFICIAL_UPDATE", "title": "Official update", "message": update.message, "status": update.status, "created_at": dt(update.created_at)})
    commitments = db.scalars(select(ResponseCommitment).where(ResponseCommitment.cluster_id == cluster.id).order_by(ResponseCommitment.created_at.desc())).all()
    for commitment in commitments:
        can_see, _ = commitment_scope(db, actor, commitment)
        if commitment.visibility != "SCHOOL" and not can_see:
            continue
        commitment_events = db.scalars(select(StatusEvent).where(StatusEvent.entity_type == "RESPONSE_COMMITMENT", StatusEvent.entity_id == commitment.id).order_by(StatusEvent.created_at.desc()).limit(20)).all()
        for event in commitment_events:
            events.append({"id": event.id, "type": "COMMITMENT_STATUS", "title": f"Commitment moved to {event.to_status.replace('_', ' ').title()}", "message": event.reason or "Response commitment status updated.", "status": event.to_status, "created_at": dt(event.created_at)})
        updates = db.scalars(select(ResponseCommitmentUpdate).where(ResponseCommitmentUpdate.commitment_id == commitment.id).order_by(ResponseCommitmentUpdate.created_at.desc()).limit(20)).all()
        for update in updates:
            if update.visibility == "SCHOOL" or can_see:
                events.append({"id": update.id, "type": "COMMITMENT_UPDATE", "title": "Response commitment update", "message": update.message, "status": commitment.status, "created_at": dt(update.created_at)})
    if not events:
        events.append({"id": f"current-{cluster.id}", "type": "CURRENT_STATUS", "title": f"Problem is {cluster.status.replace('_', ' ').title()}", "message": "This is the current recorded problem stage.", "status": cluster.status, "created_at": dt(cluster.updated_at)})
    return sorted(events, key=lambda event: event.get("created_at") or "", reverse=True)[:60]


def cluster_response_loop(db: Session, cluster: ProblemCluster, actor: User) -> dict[str, Any]:
    all_commitments = db.scalars(select(ResponseCommitment).where(ResponseCommitment.cluster_id == cluster.id).order_by(ResponseCommitment.updated_at.desc())).all()
    commitments = [item for item in all_commitments if item.visibility == "SCHOOL" or commitment_scope(db, actor, item)[0]]
    research = db.scalar(select(ResearchProject).where(ResearchProject.cluster_id == cluster.id).order_by(ResearchProject.updated_at.desc()))
    active = next((item for item in commitments if item.status not in RESPONSE_COMMITMENT_TERMINAL), None)
    selected = active or (commitments[0] if commitments else None)
    if selected and selected.status == "NOT_NOW":
        next_step = "Revisit the documented decision on the next-update date."
    elif active:
        next_step = "Follow the response commitment and wait for the next update."
    elif research:
        next_step = "Continue the linked investigation and record what the evidence supports."
    else:
        next_step = "A response owner or investigation still needs to be recorded."
    can_see_selected = selected and (selected.visibility == "SCHOOL" or commitment_scope(db, actor, selected)[0])
    return {
        "next_step": next_step,
        "needs_response": not bool(commitments or research),
        "commitment_id": selected.id if can_see_selected else None,
        "status": selected.status if can_see_selected else None,
        "owner_role": selected.owner_role if can_see_selected else None,
        "owner_name": (db.get(User, selected.owner_id).display_name if can_see_selected and selected and selected.owner_id and db.get(User, selected.owner_id) else None),
        "next_update_date": selected.next_update_date if can_see_selected else None,
        "is_stale": bool(can_see_selected and commitment_reminder(selected) and commitment_reminder(selected)[0] == "OVERDUE"),
    }


def ensure_commitment_reminders(db: Session, actor: User, commitments: list[ResponseCommitment]) -> None:
    today = date.today()
    for item in commitments:
        reminder = commitment_reminder(item)
        if not reminder or not item.owner_id:
            continue
        message = reminder[1]
        existing = db.scalar(select(Notification).where(Notification.user_id == item.owner_id, Notification.title == "Response commitment reminder", Notification.message == message, Notification.created_at >= datetime.combine(today, datetime.min.time())))
        if not existing:
            db.add(Notification(id=new_id(), user_id=item.owner_id, title="Response commitment reminder", message=message))


def has_active_role(db: Session, user: User, *roles: str) -> bool:
    allowed = {normalize_role(role) for role in roles}
    return bool(allowed.intersection(active_role_codes(db, user)))


def require_same_school(actor: User, school_id: str) -> None:
    if actor.school_id != school_id:
        raise HTTPException(status_code=404, detail="Record not found.")


def role_guard(actor: User, *roles: str) -> None:
    if actor.role not in roles:
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "You do not have permission for this action."})


def transition(db: Session, actor: User, entity: Any, entity_type: str, new_status: str, allowed: dict[str, set[str]], reason: str = "") -> None:
    current = entity.status
    if new_status not in allowed.get(current, set()):
        raise HTTPException(status_code=409, detail=f"Invalid {entity_type} transition: {current} → {new_status}.")
    entity.status = new_status
    db.add(
        StatusEvent(
            id=new_id(),
            school_id=actor.school_id,
            entity_type=entity_type,
            entity_id=entity.id,
            from_status=current,
            to_status=new_status,
            reason=reason,
            actor_id=actor.id,
        )
    )
    audit(db, actor, "STATUS_CHANGED", entity_type, entity.id, {"from": current, "to": new_status})


PROBLEM_TRANSITIONS = {
    "DRAFT": {"MODERATION_REVIEW", "PRIVATE_REVIEW", "WITHDRAWN"},
    "MODERATION_REVIEW": {"PUBLISHED", "PRIVATE_REVIEW", "CHANGES_REQUESTED", "ARCHIVED", "WITHDRAWN"},
    "PRIVATE_REVIEW": {"PUBLISHED", "CHANGES_REQUESTED", "ARCHIVED", "WITHDRAWN"},
    "CHANGES_REQUESTED": {"MODERATION_REVIEW", "PRIVATE_REVIEW", "WITHDRAWN"},
    "PUBLISHED": {"MERGED", "ARCHIVED"},
    "MERGED": {"PUBLISHED", "ARCHIVED"},
}
RESEARCH_TRANSITIONS = {"DRAFT": {"MENTOR_REVIEW"}, "CHANGES_REQUESTED": {"MENTOR_REVIEW"}, "MENTOR_REVIEW": {"APPROVED", "CHANGES_REQUESTED"}, "APPROVED": {"COLLECTING"}, "COLLECTING": {"ANALYZING"}, "ANALYZING": {"COMPLETED", "ARCHIVED"}}
IMPACT_TRANSITIONS = {"DRAFT": {"REVIEW"}, "CHANGES_REQUESTED": {"REVIEW"}, "REVIEW": {"APPROVED", "CHANGES_REQUESTED"}, "APPROVED": {"ACTIVE"}, "ACTIVE": {"PAUSED", "COMPLETED"}, "PAUSED": {"ACTIVE", "ARCHIVED"}, "COMPLETED": {"IMPACT_REVIEW"}, "IMPACT_REVIEW": {"PUBLISHED", "CHANGES_REQUESTED"}}


def sensitivity_reason(title: str, description: str) -> str | None:
    text = f"{title} {description}".lower()
    patterns = {
        "personal accusation": r"\b(accuse|accusation|harass|bully|bullying|abuse|assault)\b",
        "urgent support": r"\b(self[- ]?harm|suicide|kill myself|crisis|unsafe)\b",
        "individual complaint": r"\b(my teacher|teacher .* did|student .* did|staff .* did|[a-z]+ is a liar)\b",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text):
            return label
    return None


def ai_framing(title: str, description: str) -> dict[str, Any]:
    text = f"{title} {description}".lower()
    questions = [
        "During which weeks or period did this occur?",
        "Approximately how often did you observe the pattern?",
        "Which group or classes are affected?",
    ]
    if "deadline" in text or "assignment" in text:
        interpretation = "This may be a recurring concentration of major assignment deadlines."
    elif "queue" in text or "wait" in text:
        interpretation = "This may be a recurring wait-time or service-capacity problem."
    else:
        interpretation = "This may describe a recurring school or community experience that can be measured."
    return {"interpretation": interpretation, "clarifying_questions": questions, "confidence": 0.72, "provider": "deterministic-demo"}


def plan_missing(content: dict[str, Any]) -> list[str]:
    fields = ["question", "population", "method", "sampling", "ethics", "limitations", "conclusion_boundary"]
    return [field for field in fields if not str(content.get(field, "")).strip()]


def report_dict(db: Session, report: ProblemReport, actor: User) -> dict[str, Any]:
    author = db.get(User, report.author_id)
    reviewer = has_active_role(db, actor, "MODERATOR", "ADMIN")
    show_author = report.visibility != "SCHOOL_ANONYMOUS" or reviewer or actor.id == report.author_id
    follow_up_evidence = db.scalars(select(Evidence).where(Evidence.report_id == report.id).order_by(Evidence.created_at.desc())).all()
    can_see_follow_up = reviewer or actor.id == report.author_id
    return {
        "id": report.id,
        "title": report.title,
        "description": report.description,
        "affected_group": report.affected_group,
        "scope": report.scope,
        "category": report.category,
        "frequency": report.frequency,
        "severity": report.severity,
        "visibility": report.visibility,
        "status": report.status,
        "cluster_id": report.cluster_id,
        "author": author.display_name if show_author and author else "Anonymous student",
        "sensitivity_reason": report.sensitivity_reason if reviewer else None,
        "follow_up_evidence": [{"id": item.id, "source": item.source, "type": item.evidence_type, "observation_date": item.observation_date, "relevance": item.relevance, "visibility": item.visibility, "file_name": item.file_name} for item in follow_up_evidence] if can_see_follow_up else [],
        "created_at": dt(report.created_at),
        "updated_at": dt(report.updated_at),
    }


def evidence_is_visible(db: Session, evidence: Evidence, actor: User) -> bool:
    if evidence.visibility == "SCHOOL" or evidence.author_id == actor.id:
        return True
    return has_active_role(db, actor, "MENTOR", "OSIS", "MODERATOR", "ADMIN")


def cluster_dict(db: Session, cluster: ProblemCluster, actor: User) -> dict[str, Any]:
    reports = db.scalars(select(ProblemReport).where(ProblemReport.cluster_id == cluster.id)).all()
    signals = db.scalars(select(ProblemSignal).where(ProblemSignal.cluster_id == cluster.id)).all()
    evidence = db.scalars(select(Evidence).where(Evidence.cluster_id == cluster.id)).all()
    updates = db.scalars(select(OfficialUpdate).where(OfficialUpdate.cluster_id == cluster.id).order_by(OfficialUpdate.created_at.desc())).all()
    commitments = db.scalars(select(ResponseCommitment).where(ResponseCommitment.cluster_id == cluster.id).order_by(ResponseCommitment.updated_at.desc())).all()
    signal_counts: dict[str, int] = {}
    for signal in signals:
        signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
    reviewer = has_active_role(db, actor, "MODERATOR", "ADMIN")
    visible_reports = [r for r in reports if r.status in {"PUBLISHED", "MERGED"} or reviewer]
    visible_evidence = [item for item in evidence if evidence_is_visible(db, item, actor)]
    followed = db.scalar(select(ProblemFollow).where(ProblemFollow.cluster_id == cluster.id, ProblemFollow.user_id == actor.id)) is not None
    priority = db.scalar(select(ProblemPriority).where(ProblemPriority.cluster_id == cluster.id, ProblemPriority.school_id == actor.school_id))
    visible_commitments = [item for item in commitments if item.visibility == "SCHOOL" or commitment_scope(db, actor, item)[0]]
    priority_assessment = None
    if priority:
        reviewer_user = db.get(User, priority.reviewed_by) if priority.reviewed_by else None
        priority_assessment = {
            "priority": priority.priority,
            "evidence_strength": priority.evidence_strength,
            "urgency_score": priority.urgency_score,
            "reach_score": priority.reach_score,
            "feasibility_score": priority.feasibility_score,
            "rationale": priority.rationale,
            "reviewed_by": reviewer_user.display_name if reviewer_user else None,
            "review_date": priority.review_date,
            "reviewed_at": dt(priority.reviewed_at),
        }
    return {
        "id": cluster.id,
        "title": cluster.title,
        "summary": cluster.summary,
        "category": cluster.category,
        "scope": cluster.scope,
        "status": cluster.status,
        "affected_count": signal_counts.get("AFFECTS_ME", 0),
        "evidence_count": len(visible_evidence),
        "report_count": len(visible_reports),
        "followed": followed,
        "priority": priority.priority if priority else None,
        "priority_rationale": priority.rationale if priority else cluster.priority_rationale,
        "priority_assessment": priority_assessment,
        "signal_counts": signal_counts,
        "reports": [report_dict(db, r, actor) for r in visible_reports],
        "evidence": [{"id": e.id, "source": e.source, "type": e.evidence_type, "observation_date": e.observation_date, "relevance": e.relevance, "visibility": e.visibility, "file_name": e.file_name} for e in visible_evidence],
        "official_updates": [{"id": u.id, "status": u.status, "message": u.message, "created_at": dt(u.created_at)} for u in updates if u.status == "PUBLISHED" or reviewer or u.author_id == actor.id],
        "response_commitments": [commitment_dict(db, item, actor) for item in visible_commitments],
        "response_loop": cluster_response_loop(db, cluster, actor),
        "timeline": cluster_timeline(db, cluster, actor),
        "needs_response": not bool(commitments or db.scalar(select(ResearchProject.id).where(ResearchProject.cluster_id == cluster.id))),
        "created_at": dt(cluster.created_at),
        "updated_at": dt(cluster.updated_at),
    }


def research_dict(db: Session, research: ResearchProject) -> dict[str, Any]:
    versions = db.scalars(select(ResearchPlanVersion).where(ResearchPlanVersion.research_id == research.id).order_by(ResearchPlanVersion.version.desc())).all()
    plan = versions[0].content if versions else {}
    reviews = db.scalars(select(Review).where(Review.entity_type == "RESEARCH_PROJECT", Review.entity_id == research.id).order_by(Review.created_at.desc())).all()
    leader = db.get(User, research.leader_id)
    mentor = db.get(User, research.mentor_id) if research.mentor_id else None
    return {"id": research.id, "title": research.title, "cluster_id": research.cluster_id, "leader_id": research.leader_id, "leader_name": leader.display_name if leader else None, "mentor_id": research.mentor_id, "mentor_name": mentor.display_name if mentor else None, "status": research.status, "plan": plan, "plan_version": versions[0].version if versions else 0, "plan_immutable": versions[0].immutable if versions else False, "missing_sections": plan_missing(plan), "versions": [{"version": version.version, "submitted": version.submitted, "immutable": version.immutable, "created_at": dt(version.created_at), "content": version.content} for version in versions], "review_history": [{"id": review.id, "decision": review.decision, "reason": review.reason, "reviewed_version": review.reviewed_version, "reviewer_id": review.reviewer_id, "created_at": dt(review.created_at)} for review in reviews], "created_at": dt(research.created_at), "updated_at": dt(research.updated_at)}


def impact_dict(db: Session, project: ImpactProject) -> dict[str, Any]:
    metrics = db.scalars(select(Metric).where(Metric.project_id == project.id, Metric.active.is_(True))).all()
    metric_rows = []
    for metric in metrics:
        observations = db.scalars(select(Observation).where(Observation.metric_id == metric.id).order_by(Observation.observed_on)).all()
        baseline = next((o for o in observations if o.phase == "BASELINE"), None)
        post = next((o for o in observations if o.phase == "POST"), None)
        change = None
        pct = None
        if baseline and post:
            change = post.value - baseline.value
            pct = round((change / baseline.value) * 100, 2) if baseline.value else None
        metric_rows.append({"id": metric.id, "name": metric.name, "description": metric.description, "unit": metric.unit, "direction": metric.direction, "target": metric.target, "is_primary": metric.is_primary, "observations": [{"id": o.id, "phase": o.phase, "value": o.value, "observed_on": o.observed_on, "sample_size": o.sample_size, "notes": o.notes} for o in observations], "observed_change": change, "observed_change_percent": pct})
    tasks = db.scalars(select(ProjectTask).where(ProjectTask.project_id == project.id)).all()
    report = db.scalars(select(ImpactReport).where(ImpactReport.project_id == project.id).order_by(ImpactReport.version.desc())).first()
    return {"id": project.id, "title": project.title, "research_id": project.research_id, "cluster_id": project.cluster_id, "leader_id": project.leader_id, "mentor_id": project.mentor_id, "status": project.status, "target_users": project.target_users, "intervention": project.intervention, "theory_of_change": project.theory_of_change, "risks": project.risks, "resources": project.resources, "metrics": metric_rows, "tasks": [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "due_date": t.due_date, "owner_id": t.owner_id, "project_id": t.project_id, "href": f"/app/projects/{t.project_id}"} for t in tasks], "report": report.content if report else None, "report_version": report.version if report else 0, "created_at": dt(project.created_at), "updated_at": dt(project.updated_at)}


def seed_demo() -> None:
    if os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower() in {"production", "prod"}:
        raise RuntimeError("Development seed data is disabled in production.")
    db = SessionLocal()
    try:
        school = db.get(School, "school-pilar")
        if not school:
            school = School(id="school-pilar", name="Sekolah Pilar Indonesia", slug="pilar-impact-lab", mode=os.getenv("APP_MODE", "DEMO"), language="en", is_active=True)
            db.add(school)
            db.add(SchoolSetting(school_id=school.id, settings={"school_name": school.name, "urgent_help_notice": "ImpactOS is not an emergency channel. Contact the school's designated safeguarding team for urgent help.", "private_report_owner_role": "ADMIN", "allowed_categories": ["ACADEMICS", "CAMPUS", "WELLBEING", "ENVIRONMENT"], "retention_reference": "To be confirmed with Pilar", "publication_policy": "School-only during closed alpha"}))
        demo_users = [
            ("user-student", "student@demo.local", "Aisha Student", "STUDENT"),
            ("user-leader", "leader@demo.local", "Rafi Project Leader", "STUDENT_LEADER"),
            ("user-mentor", "mentor@demo.local", "Ms. Rani Mentor", "MENTOR"),
            ("user-osis", "osis@demo.local", "Dimas OSIS Reviewer", "OSIS"),
            ("user-moderator", "moderator@demo.local", "Nadia Moderator", "MODERATOR"),
            ("user-admin", "admin@demo.local", "Pilar Administrator", "ADMIN"),
            ("user-multi", "multi@demo.local", "Sam Multi Role", "STUDENT_LEADER"),
        ]
        users: dict[str, User] = {}
        for uid, email, name, role in demo_users:
            user = db.get(User, uid)
            if not user:
                user = User(id=uid, school_id=school.id, email=email, display_name=name, role=role, password_hash=hash_password(DEMO_PASSWORD), active=True)
                db.add(user)
            if getattr(user, "status", None) is None:
                user.status = "ACTIVE"
            if not user.active:
                user.active = True
            users[email] = user
        db.flush()
        for user in users.values():
            roles = ["STUDENT_PROJECT_LEADER", "MENTOR"] if user.email == "multi@demo.local" else [normalize_role(user.role)]
            ensure_identity_records(db, user, roles)
        db.flush()
        admin = users["admin@demo.local"]
        invitation_seed = [
            ("invitation-pending", "pending@demo.local", "PENDING", datetime.utcnow() + timedelta(days=7), "demo-pending-invitation-token"),
            ("invitation-expired", "expired@demo.local", "EXPIRED", datetime.utcnow() - timedelta(days=1), "demo-expired-invitation-token"),
            ("invitation-revoked", "revoked@demo.local", "REVOKED", datetime.utcnow() + timedelta(days=7), "demo-revoked-invitation-token"),
        ]
        for invitation_id, email, invitation_status, expires_at, raw_token in invitation_seed:
            if not db.get(Invitation, invitation_id):
                invitation = Invitation(id=invitation_id, school_id=school.id, email=email, role="STUDENT", token_hash=secure_token_hash(raw_token), expires_at=expires_at, status=invitation_status, revoked_at=datetime.utcnow() if invitation_status == "REVOKED" else None, created_by=admin.id, invited_by=admin.id)
                db.add(invitation)
                db.flush()
                role = db.scalar(select(Role).where(Role.code == "STUDENT_CONTRIBUTOR"))
                if role:
                    db.add(InvitationRole(invitation_id=invitation.id, role_id=role.id))
        clusters = [
            ("cluster-assessment", "Assessment Workload Concentration", "Major assignments are often due within the same three-day period across Grade 10 classes.", "ACADEMICS", "Several Grade 10 classes", "VALIDATED"),
            ("cluster-canteen", "Canteen Queue Congestion", "Students report long queues during the main lunch window.", "CAMPUS", "Main canteen", "GATHERING_EVIDENCE"),
            ("cluster-study", "Quiet Study-Space Availability", "Students have difficulty finding a quiet place to study after class.", "CAMPUS", "Secondary library area", "UNDER_INVESTIGATION"),
        ]
        for cid, title, summary, category, scope, state in clusters:
            if not db.get(ProblemCluster, cid):
                db.add(ProblemCluster(id=cid, school_id=school.id, title=title, summary=summary, category=category, scope=scope, status=state))
        db.flush()
        if not db.get(ProblemReport, "report-assessment"):
            db.add(ProblemReport(id="report-assessment", school_id=school.id, author_id=users["student@demo.local"].id, title="Major assignments overlap", description="In several Grade 10 classes, major assignments are repeatedly due within the same three-day period.", affected_group="Grade 10 students", scope="Several classes", category="ACADEMICS", frequency="Several times this term", severity="MEDIUM", visibility="SCHOOL_NAMED", status="PUBLISHED", cluster_id="cluster-assessment"))
        if not db.get(ProblemReport, "report-private"):
            db.add(ProblemReport(id="report-private", school_id=school.id, author_id=users["student@demo.local"].id, title="Private concern for designated staff", description="This synthetic report demonstrates restricted moderation handling.", affected_group="One student", scope="Private", category="WELLBEING", visibility="PRIVATE_REVIEW", status="PRIVATE_REVIEW", sensitivity_reason="synthetic private-review fixture"))
        if not db.get(ProblemSignal, "signal-assessment-student"):
            for sid, email, signal in [("signal-assessment-student", "student@demo.local", "AFFECTS_ME"), ("signal-assessment-leader", "leader@demo.local", "WANTS_TO_INVESTIGATE"), ("signal-assessment-mentor", "mentor@demo.local", "HAS_EVIDENCE")]:
                db.add(ProblemSignal(id=sid, cluster_id="cluster-assessment", user_id=users[email].id, signal_type=signal))
        if not db.get(Evidence, "evidence-assessment"):
            db.add(Evidence(id="evidence-assessment", school_id=school.id, author_id=users["leader@demo.local"].id, cluster_id="cluster-assessment", source="Synthetic timetable observation", evidence_type="OBSERVATION", observation_date="2026-08-10", relevance="Four major deadlines fell inside two three-day windows.", visibility="SCHOOL"))
        if not db.get(ResearchProject, "research-assessment"):
            research = ResearchProject(id="research-assessment", school_id=school.id, cluster_id="cluster-assessment", leader_id=users["leader@demo.local"].id, title="Deadline concentration study", status="APPROVED", mentor_id=users["mentor@demo.local"].id)
            db.add(research)
            db.flush()
            db.add(ResearchPlanVersion(id="plan-assessment-v1", research_id=research.id, version=1, content={"question": "How concentrated are major assignment deadlines across Grade 10 classes during a typical month?", "question_type": "descriptive", "hypothesis": "", "population": "Grade 10 classes in the pilot", "variables": [{"name": "major deadlines", "definition": "Count of deadlines in a three-day window"}], "method": "Descriptive review of synthetic assessment dates", "sampling": "All pilot classes", "data_collection": "Date extraction", "ethics": "Use aggregate dates only; no student performance records", "limitations": "Synthetic dates do not represent actual Pilar findings.", "conclusion_boundary": "Describe deadline concentration only; do not claim impact on grades."}, submitted=True, immutable=True, created_by=research.leader_id))
        if not db.get(Survey, "survey-assessment"):
            db.add(Survey(id="survey-assessment", school_id=school.id, research_id="research-assessment", title="Assessment workload check", purpose="Understand when students experience deadline concentration.", privacy_mode="ANONYMOUS", status="OPEN", code="demo-assessment", one_response=True, created_by=users["leader@demo.local"].id))
            db.add(SurveyQuestion(id="survey-q1", survey_id="survey-assessment", position=1, question_type="LIKERT", prompt="How often do major deadlines overlap for you?", options=["Never", "Rarely", "Sometimes", "Often", "Always"], required=True))
        if not db.get(ImpactProject, "impact-calendar"):
            project = ImpactProject(id="impact-calendar", school_id=school.id, research_id="research-assessment", cluster_id="cluster-assessment", leader_id=users["leader@demo.local"].id, mentor_id=users["mentor@demo.local"].id, title="Shared Assessment Calendar", target_users="Grade 10 teaching teams", intervention="Create a shared view of major assessment dates.", theory_of_change="If teachers can see deadline conflicts before publishing, then concentrated windows may decrease.", risks="Calendar maintenance may be inconsistent.", resources="Shared calendar and weekly review", status="ACTIVE")
            db.add(project)
            db.flush()
            db.add(Metric(id="metric-calendar", project_id=project.id, name="Major deadlines inside a three-day window", description="Count of major deadlines per three-day window", unit="count", direction="DECREASE", collection_method="Review synthetic assessment dates", target=3, is_primary=True))
            db.add(Observation(id="obs-calendar-baseline", metric_id="metric-calendar", project_id=project.id, phase="BASELINE", value=8, observed_on="2026-08-01", sample_size=14, notes="Synthetic pre-intervention observation", recorder_id=project.leader_id))
            db.add(Observation(id="obs-calendar-post", metric_id="metric-calendar", project_id=project.id, phase="POST", value=5, observed_on="2026-08-22", sample_size=14, notes="Synthetic post-intervention observation; not causal proof", recorder_id=project.leader_id))
            db.add(ImpactReport(id="report-calendar-v1", project_id=project.id, version=1, immutable=True, created_by=project.leader_id, content={"problem": "Assessment Workload Concentration", "research_question": "How concentrated are major assignment deadlines across Grade 10 classes during a typical month?", "intervention": "Shared Assessment Calendar", "results": "Observed change from 8 to 5 deadlines in the selected three-day-window measure.", "limitations": "Synthetic data and a simple before/after comparison do not establish causation.", "what_did_not_work": "The calendar did not eliminate all overlap.", "next_steps": "Test with a larger approved pilot cohort."}))
        if not db.get(ImpactProject, "impact-study-space"):
            db.add(ImpactProject(id="impact-study-space", school_id=school.id, research_id=None, cluster_id="cluster-study", leader_id=users["student@demo.local"].id, mentor_id=users["mentor@demo.local"].id, title="Quiet Study Space Pilot", target_users="Students after class", intervention="Pilot a reservable quiet zone.", theory_of_change="", risks="", resources="", status="REVIEW"))
        if not db.scalar(select(PublicImpactStory).where(PublicImpactStory.slug == "shared-assessment-calendar")):
            db.add(PublicImpactStory(id="public-story-calendar", school_id=school.id, source_project_id="impact-calendar", slug="shared-assessment-calendar", title="Making assessment timing easier to see", problem_summary="A synthetic pilot examined whether major assignment deadlines were concentrated inside the same three-day windows.", evidence_summary="The team reviewed synthetic assessment dates for the closed-alpha scenario.", research_question="How concentrated are major assignment deadlines across Grade 10 classes during a typical month?", intervention_summary="A shared assessment calendar made upcoming major deadlines visible to the participating teaching team.", measurement_summary="The team compared a pre-intervention baseline with a later observation using one declared count measure.", observed_result="The selected synthetic measure changed from 8 to 5 deadlines in a three-day window. This is an observed change, not proof of causation.", limitations="The example uses synthetic data and a simple before/after comparison; it does not represent an SPI finding.", what_did_not_work="The calendar did not eliminate every overlap and depended on consistent updates.", next_steps="If the school approves a live pilot, confirm the measurement design and governance rules first.", official_response="Synthetic example prepared for closed-alpha demonstration.", category="ACADEMICS", result_type="MIXED", status="PUBLISHED", public_team_label="Synthetic student project team", is_synthetic=True, approved_by=users["admin@demo.local"].id, approved_at=datetime.utcnow(), published_by=users["admin@demo.local"].id, published_at=datetime.utcnow()))

        # Connected closed-alpha scenario: student observations → moderation →
        # validated problem → research review → planned intervention → OSIS update.
        canteen = db.get(ProblemCluster, "cluster-canteen")
        if canteen:
            canteen.title = "Long canteen queues during the second break"
            canteen.summary = "Students report that the main canteen queue regularly exceeds a reasonable waiting time during the second break."
            canteen.category = "FACILITIES"
            canteen.scope = "Main canteen · second break"
            canteen.status = "VALIDATED"
        db.flush()
        canteen_reports = [
            ("report-canteen-1", "user-student", "Queue reaches the hallway during second break", "PUBLISHED", "SCHOOL_NAMED"),
            ("report-canteen-2", "user-student", "Waiting for lunch takes most of second break", "MERGED", "SCHOOL_ANONYMOUS"),
            ("report-canteen-3", "user-leader", "The ordering line slows down at the drink station", "MERGED", "SCHOOL_NAMED"),
            ("report-canteen-4", "user-multi", "Canteen queue is longest on club days", "PUBLISHED", "SCHOOL_ANONYMOUS"),
            ("report-canteen-5", "user-student", "Students skip lunch when the line is too long", "PUBLISHED", "SCHOOL_ANONYMOUS"),
            ("report-canteen-6", "user-leader", "Second break queue needs a measured baseline", "MODERATION_REVIEW", "SCHOOL_NAMED"),
            ("report-canteen-7", "user-student", "Private synthetic report for restricted review", "PRIVATE_REVIEW", "PRIVATE_REVIEW"),
        ]
        for report_id, author_id, title, state, visibility in canteen_reports:
            report = db.get(ProblemReport, report_id)
            if not report:
                report = ProblemReport(id=report_id, school_id=school.id, author_id=author_id, title=title, description="Synthetic students observed a recurring canteen waiting pattern during the second break; this record exists only for closed-alpha testing.", affected_group="Students using the main canteen", scope="Second break", category="FACILITIES", frequency="Most school days", severity="MEDIUM", visibility=visibility, status=state, cluster_id="cluster-canteen", sensitivity_reason="synthetic restricted fixture" if state == "PRIVATE_REVIEW" else None)
                db.add(report)
            else:
                report.cluster_id = "cluster-canteen"
                report.status = state
                report.visibility = visibility
        db.flush()
        for signal_id, user_id, signal_type in [
            ("signal-canteen-aisha", "user-student", "AFFECTS_ME"),
            ("signal-canteen-leader", "user-leader", "WANTS_TO_INVESTIGATE"),
            ("signal-canteen-multi", "user-multi", "HAS_EVIDENCE"),
        ]:
            if not db.get(ProblemSignal, signal_id):
                db.add(ProblemSignal(id=signal_id, cluster_id="cluster-canteen", user_id=user_id, signal_type=signal_type))
        for evidence_id, source, relevance in [
            ("evidence-canteen-queue", "Synthetic queue observation sheet", "Seven closed-alpha observations describe second-break waiting time without collecting student names."),
            ("evidence-canteen-lane", "Synthetic canteen layout note", "The drink station is a visible bottleneck to test in a future approved pilot."),
        ]:
            if not db.get(Evidence, evidence_id):
                db.add(Evidence(id=evidence_id, school_id=school.id, author_id=users["leader@demo.local"].id, cluster_id="cluster-canteen", source=source, evidence_type="OBSERVATION", observation_date="2026-08-20", relevance=relevance, visibility="SCHOOL"))
        for follow_id, user_id in [("follow-canteen-aisha", "user-student"), ("follow-canteen-leader", "user-leader")]:
            existing_follow = db.scalar(select(ProblemFollow).where(ProblemFollow.cluster_id == "cluster-canteen", ProblemFollow.user_id == user_id))
            if not existing_follow:
                db.add(ProblemFollow(id=follow_id, cluster_id="cluster-canteen", user_id=user_id))
        if not db.get(ResearchProject, "research-canteen"):
            db.add(ResearchProject(id="research-canteen", school_id=school.id, cluster_id="cluster-canteen", leader_id=users["leader@demo.local"].id, title="Investigating average canteen waiting time", status="MENTOR_REVIEW", mentor_id=users["mentor@demo.local"].id))
            db.flush()
            plan_content = {"question": "What is the median student waiting time at the main canteen during the second break?", "question_type": "descriptive", "purpose": "Describe the queue pattern before choosing an intervention.", "population": "Students using the main canteen during the second break", "method": "Time-stamped observation at the queue entrance and service point", "sampling": "Four second-break observations across two school days", "data_collection": "Aggregate minutes only; no student names or purchase details", "ethics": "Do not photograph faces or collect identifying information; tell students the observation is synthetic for this closed alpha.", "limitations": "The small synthetic observation window cannot represent all school days.", "conclusion_boundary": "Describe observed waiting time; do not claim a cause or universal student experience."}
            db.add(ResearchPlanVersion(id="plan-canteen-v1", research_id="research-canteen", version=1, content={**plan_content, "sampling": "One second-break observation only; revise before any real pilot."}, submitted=True, immutable=True, created_by=users["leader@demo.local"].id))
            db.add(ResearchPlanVersion(id="plan-canteen-v2", research_id="research-canteen", version=2, content=plan_content, submitted=True, immutable=False, created_by=users["leader@demo.local"].id))
            db.add(Review(id="review-canteen-changes", school_id=school.id, entity_type="RESEARCH_PROJECT", entity_id="research-canteen", reviewer_id=users["mentor@demo.local"].id, decision="REQUEST_CHANGES", reason="Please revise the sampling method so observations cover more than one second break.", reviewed_version=1))
        if not db.get(ImpactProject, "impact-canteen"):
            db.add(ImpactProject(id="impact-canteen", school_id=school.id, research_id="research-canteen", cluster_id="cluster-canteen", leader_id=users["leader@demo.local"].id, mentor_id=users["mentor@demo.local"].id, title="Staggered ordering lane pilot", target_users="Students using the main canteen during second break", intervention="Test a clearly marked staggered ordering lane after the baseline is approved.", theory_of_change="If service flow is separated at the drink station, median waiting time may decrease.", risks="A changed queue may shift congestion elsewhere; the pilot must be monitored.", resources="Canteen staff agreement, observation sheet, temporary signs", status="PLANNING"))
            db.flush()
            db.add(Metric(id="metric-canteen-wait", project_id="impact-canteen", name="Median canteen waiting time", description="Median observed waiting time from joining the queue to receiving an order.", unit="minutes", direction="DECREASE", collection_method="Anonymous time-stamped observations", target=7, is_primary=True))
            for task_id, title, owner_id, due_date in [("task-canteen-schedule", "Confirm observation schedule", "user-leader", "2026-09-02"), ("task-canteen-sampling", "Revise sampling method", "user-leader", "2026-09-03"), ("task-canteen-baseline", "Collect baseline observations", "user-multi", "2026-09-05"), ("task-canteen-update", "Prepare OSIS update", "user-osis", "2026-09-06")]:
                db.add(ProjectTask(id=task_id, project_id="impact-canteen", title=title, owner_id=owner_id, status="TODO", priority="HIGH" if "baseline" in task_id else "MEDIUM", due_date=due_date))
        if not db.get(ResponseCommitment, "commitment-canteen-response"):
            db.add(ResponseCommitment(id="commitment-canteen-response", school_id=school.id, cluster_id="cluster-canteen", research_id="research-canteen", project_id="impact-canteen", title="Confirm a fair second-break queue response", intended_outcome="Agree whether a staggered ordering lane can be tested after the research and baseline gates are complete.", owner_role="OSIS_REVIEWER", owner_id=users["osis@demo.local"].id, assigned_by=users["admin@demo.local"].id, status="IN_PROGRESS", priority="HIGH", due_date="2026-09-06", next_update_date="2026-09-01", visibility="SCHOOL"))
            db.flush()
            db.add(ResponseCommitmentUpdate(id="commitment-update-canteen-1", school_id=school.id, commitment_id="commitment-canteen-response", author_id=users["osis@demo.local"].id, kind="UPDATE", message="OSIS is reviewing the validated concern and will publish the next decision after the research sampling is revised.", visibility="SCHOOL"))
        if not db.get(OfficialUpdate, "update-canteen-draft"):
            db.add(OfficialUpdate(id="update-canteen-draft", school_id=school.id, cluster_id="cluster-canteen", author_id=users["osis@demo.local"].id, status="DRAFT", message="The OSIS team is reviewing a validated synthetic concern about second-break canteen waiting time. No intervention result has been claimed."))
        db.flush()
        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    validate_security_config()
    init_db()
    seed_enabled = os.getenv("DEVELOPMENT_SEED_ENABLED", "true" if app_mode() == "DEMO" else "false").lower() == "true"
    if seed_enabled and os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower() not in {"production", "prod"}:
        seed_demo()


@app.get(f"{API}/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "impactos-api", "mode": app_mode(), "synthetic_data": app_mode() == "DEMO"}


@app.get(f"{API}/ready")
def ready(db: Session = Depends(get_db)) -> dict[str, Any]:
    db.execute(select(func.count()).select_from(School))
    return {"status": "ready", "database": "ok"}


@app.get(f"{API}/public/site")
def public_site() -> dict[str, Any]:
    return {
        "institution": "Sekolah Pilar Indonesia",
        "product": "Pilar Impact Lab",
        "powered_by": "ImpactOS",
        "official_site_url": "https://sekolah-pilar-indonesia.sch.id/",
        "mode": app_mode(),
        "demo_access_allowed": demo_access_allowed(),
        "synthetic_notice": "Pilar Impact Lab is currently being developed and tested with synthetic data." if app_mode() in {"DEMO", "CLOSED_ALPHA"} else None,
        "contact": {"status": "PENDING_SCHOOL_CONFIRMATION", "message": "Contact information will be published after the school confirms the pilot support route."},
    }


@app.get(f"{API}/public/faq")
def public_faq() -> list[dict[str, str]]:
    return PUBLIC_FAQ


@app.get(f"{API}/public/impact-stories")
def public_impact_stories(search: str | None = None, category: str | None = None, result_type: str | None = None, db: Session = Depends(get_db)) -> dict[str, Any]:
    query = select(PublicImpactStory).where(PublicImpactStory.status == "PUBLISHED")
    if search:
        term = f"%{search.strip()}%"
        query = query.where(PublicImpactStory.title.ilike(term) | PublicImpactStory.problem_summary.ilike(term))
    if category:
        query = query.where(PublicImpactStory.category == category.upper())
    if result_type:
        query = query.where(PublicImpactStory.result_type == result_type.upper())
    stories = db.scalars(query.order_by(PublicImpactStory.published_at.desc())).all()
    return {"items": [public_story_dict(story) for story in stories], "total": len(stories), "synthetic_data": app_mode() == "DEMO"}


@app.get(f"{API}/public/impact-stories/{{slug}}")
def public_impact_story(slug: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    story = db.scalar(select(PublicImpactStory).where(PublicImpactStory.slug == slug, PublicImpactStory.status == "PUBLISHED"))
    if not story:
        raise HTTPException(404, "Impact story not found.")
    return public_story_dict(story)


@app.post(f"{API}/auth/login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    enforce_rate_limit(request, "login", limit=10, window_seconds=300)
    normalized_email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user and user.email.endswith("@demo.local") and not demo_access_allowed():
        user = None
    valid = user and user.active and getattr(user, "status", "ACTIVE") == "ACTIVE" and verify_password(payload.password, user.password_hash)
    if not valid:
        audit(db, user, "AUTH_LOGIN_FAILED", "USER", user.id if user else None, {"reason": "invalid_credentials"}, request=request)
        db.commit()
        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "The email or password is incorrect."})
    if password_needs_upgrade(user.password_hash):
        user.password_hash = hash_password(payload.password)
    user.status = "ACTIVE"
    user.last_login_at = datetime.utcnow()
    ensure_identity_records(db, user)
    session, csrf = create_session(user, db, request)
    audit(db, user, "AUTH_LOGIN_SUCCEEDED", "USER", user.id, request=request)
    db.commit()
    summary = user_dict(user)
    summary.update({"roles": active_role_codes(db, user), "permissions": active_permissions(db, user)})
    response.set_cookie(SESSION_COOKIE, session, **session_cookie_options())
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **{key: value for key, value in session_cookie_options().items() if key != "httponly"})
    return {"user": summary, "mode": app_mode(), "synthetic_data": app_mode() == "DEMO"}


@app.post(f"{API}/auth/logout", dependencies=[Depends(require_csrf)])
def logout(request: Request, response: Response, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    auth_session = getattr(request.state, "auth_session", None)
    if auth_session:
        revoke_session(auth_session)
        audit(db, actor, "AUTH_SESSION_REVOKED", "SESSION", auth_session.id, {"reason": "logout"}, request=request)
    audit(db, actor, "AUTH_LOGOUT", "USER", actor.id, request=request)
    db.commit()
    response.delete_cookie(SESSION_COOKIE, secure=session_cookie_options()["secure"], httponly=True, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, secure=session_cookie_options()["secure"], httponly=False, samesite="lax")
    return {"status": "logged_out"}


@app.get(f"{API}/me", response_model=UserRead)
def me(actor: User = Depends(get_current_user)) -> User:
    return actor


@app.get(f"{API}/auth/me", response_model=AuthMeResponse)
def auth_me(db: Session = Depends(get_db), actor: User = Depends(get_current_user)) -> dict[str, Any]:
    payload = auth_me_dict(db, actor)
    db.commit()
    return payload


@app.get(f"{API}/auth/session")
def auth_session(actor: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"authenticated": True, "user": user_dict(actor)}


def invitation_state(invitation: Invitation) -> str:
    if invitation.revoked_at or getattr(invitation, "status", "PENDING") == "REVOKED":
        return "REVOKED"
    if invitation.used_at or getattr(invitation, "status", "PENDING") == "USED":
        return "USED"
    if invitation.expires_at <= datetime.utcnow():
        return "EXPIRED"
    return "ACTIVE"


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked = "•" * len(local)
    else:
        masked = f"{local[0]}{'•' * max(1, len(local) - 2)}{local[-1]}"
    return f"{masked}@{domain}"


@app.get(f"{API}/auth/invitations/verify")
@app.get(f"{API}/invitations/{{token}}/preview")
def preview_invitation(token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    invitation = db.scalar(select(Invitation).where(Invitation.token_hash == secure_token_hash(token)))
    if not invitation:
        raise HTTPException(404, detail={"code": "INVITATION_INVALID", "message": "This invitation is not valid."})
    state = invitation_state(invitation)
    if state != "ACTIVE":
        code = {"EXPIRED": "INVITATION_EXPIRED", "USED": "INVITATION_USED", "REVOKED": "INVITATION_REVOKED"}.get(state, "INVITATION_INVALID")
        raise HTTPException(410, detail={"code": code, "message": "This invitation is no longer available."})
    school = db.get(School, invitation.school_id)
    role_rows = db.execute(select(Role.code).join(InvitationRole, InvitationRole.role_id == Role.id).where(InvitationRole.invitation_id == invitation.id)).all()
    roles = [row[0] for row in role_rows] or [normalize_role(invitation.role)]
    return {"email": invitation.email, "role": invitation.role, "roles": roles, "school_name": school.name if school else "Sekolah Pilar Indonesia", "expires_at": dt(invitation.expires_at), "status": state, "state": state}


@app.post(f"{API}/auth/activate")
@app.post(f"{API}/invitations/{{token}}/accept")
def accept_invitation(token: str, payload: InvitationAccept, request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    enforce_rate_limit(request, "activation", limit=8, window_seconds=900)
    invitation = db.scalar(select(Invitation).where(Invitation.token_hash == secure_token_hash(token)))
    if not invitation or invitation_state(invitation) != "ACTIVE":
        raise HTTPException(410, detail={"code": "INVITATION_INVALID", "message": "This invitation is no longer available."})
    if payload.email and payload.email.lower().strip() != invitation.email.lower().strip():
        raise HTTPException(400, detail={"code": "INVITATION_EMAIL_MISMATCH", "message": "Use the SPI email assigned to this invitation."})
    if payload.password_confirmation is not None and payload.password_confirmation != payload.password:
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "Passwords do not match.", "field_errors": {"password_confirmation": "Passwords do not match."}})
    if not payload.accepted_rules:
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "You must accept the platform rules to activate an account."})
    existing = db.scalar(select(User).where(User.email == invitation.email.lower().strip()))
    if existing and existing.active and getattr(existing, "status", "ACTIVE") == "ACTIVE":
        raise HTTPException(409, detail={"code": "ACCOUNT_EXISTS", "message": "This member account already exists. Please sign in."})
    role_rows = db.execute(select(Role.code).join(InvitationRole, InvitationRole.role_id == Role.id).where(InvitationRole.invitation_id == invitation.id)).all()
    role_codes = [row[0] for row in role_rows] or [normalize_role(invitation.role)]
    legacy_role = {"STUDENT_CONTRIBUTOR": "STUDENT", "STUDENT_PROJECT_LEADER": "STUDENT_LEADER", "OSIS_REVIEWER": "OSIS", "ADMINISTRATOR": "ADMIN"}.get(role_codes[0], role_codes[0])
    user = existing or User(id=new_id(), school_id=invitation.school_id, email=invitation.email.lower().strip(), display_name=payload.display_name.strip(), role=legacy_role, password_hash=hash_password(payload.password), active=True)
    user.display_name = payload.display_name.strip()
    user.role = legacy_role
    user.password_hash = hash_password(payload.password)
    user.active = True
    user.status = "ACTIVE"
    db.add(user)
    db.flush()
    ensure_identity_records(db, user, role_codes)
    invitation.used_at = datetime.utcnow()
    invitation.used_by = user.id
    invitation.status = "USED"
    audit(db, user, "ACCOUNT_ACTIVATED", "USER", user.id, {"roles": role_codes}, request=request)
    audit(db, user, "INVITATION_USED", "INVITATION", invitation.id, {"roles": role_codes}, request=request)
    session, csrf = create_session(user, db, request)
    db.commit()
    response.set_cookie(SESSION_COOKIE, session, **session_cookie_options())
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **{key: value for key, value in session_cookie_options().items() if key != "httponly"})
    summary = user_dict(user)
    summary.update({"roles": role_codes, "permissions": active_permissions(db, user)})
    return {"user": summary, "mode": app_mode()}


@app.post(f"{API}/activation/request-email")
def request_email_activation(payload: ActivationEmailRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    # The closed alpha intentionally does not pretend to send mail. The response
    # is neutral to avoid account/domain enumeration.
    enforce_rate_limit(request, "activation-email", limit=5, window_seconds=900)
    normalized = payload.email.strip().lower()
    configured_domains = [d.strip().lower() for d in os.getenv("APPROVED_EMAIL_DOMAINS", "").split(",") if d.strip()]
    if configured_domains and normalized.rsplit("@", 1)[-1] in configured_domains:
        audit(db, None, "ACTIVATION_EMAIL_REQUESTED", "ACTIVATION", None, request=request)
        db.commit()
    return {"message": "If this address is eligible, activation instructions will be sent by the school. If no school email activation is configured, ask an administrator for an invitation."}


@app.post(f"{API}/auth/forgot-password")
def forgot_password(payload: PasswordForgotRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    enforce_rate_limit(request, "password-recovery", limit=5, window_seconds=900)
    user = db.scalar(select(User).where(User.email == payload.email.strip().lower(), User.active.is_(True)))
    result: dict[str, Any] = {"message": "If the account can use password recovery, instructions will be provided through the configured school channel."}
    if user and app_mode() == "DEMO" and demo_access_allowed():
        raw = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(id=new_id(), user_id=user.id, token_hash=secure_token_hash(raw), expires_at=datetime.utcnow() + timedelta(minutes=30)))
        db.commit()
        result["development_reset_token"] = raw
    return result


@app.post(f"{API}/auth/reset-password")
def reset_password(payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    enforce_rate_limit(request, "password-reset", limit=8, window_seconds=900)
    reset = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == secure_token_hash(payload.token)))
    if not reset or reset.used_at or reset.expires_at <= datetime.utcnow():
        raise HTTPException(400, "This password reset link is unavailable or has expired.")
    user = db.get(User, reset.user_id)
    if not user or not user.active:
        raise HTTPException(400, "This password reset link is unavailable or has expired.")
    user.password_hash = hash_password(payload.password)
    reset.used_at = datetime.utcnow()
    audit(db, user, "PASSWORD_RESET", "USER", user.id)
    db.commit()
    return {"message": "Your password was updated. You can now sign in."}


@app.get(f"{API}/dashboard")
def dashboard(workspace: str | None = None, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    school = db.get(School, actor.school_id)
    active_roles = active_role_codes(db, actor)
    selected_role = normalize_role(workspace) if workspace and normalize_role(workspace) in active_roles else active_roles[0] if active_roles else "STUDENT_CONTRIBUTOR"
    role_name, role_description = ROLE_DETAILS.get(selected_role, (selected_role.replace("_", " ").title(), "Member workspace"))

    own_reports = db.scalars(select(ProblemReport).where(ProblemReport.school_id == actor.school_id, ProblemReport.author_id == actor.id).order_by(ProblemReport.updated_at.desc()).limit(6)).all()
    followed_clusters = db.scalars(select(ProblemCluster).join(ProblemFollow, ProblemFollow.cluster_id == ProblemCluster.id).where(ProblemFollow.user_id == actor.id, ProblemCluster.school_id == actor.school_id).order_by(ProblemCluster.updated_at.desc()).limit(6)).all()
    own_tasks = db.scalars(select(ProjectTask).where(ProjectTask.owner_id == actor.id).order_by(ProjectTask.due_date, ProjectTask.title).limit(8)).all()
    manager_view = selected_role in {"MENTOR", "OSIS_REVIEWER", "ADMINISTRATOR"}
    commitment_query = select(ResponseCommitment).where(ResponseCommitment.school_id == actor.school_id)
    if not manager_view:
        commitment_query = commitment_query.where(ResponseCommitment.owner_id == actor.id)
    response_commitments = db.scalars(commitment_query.order_by(ResponseCommitment.due_date, ResponseCommitment.next_update_date, ResponseCommitment.title).limit(12)).all()
    ensure_commitment_reminders(db, actor, response_commitments)
    leader_research = db.scalars(select(ResearchProject).where(ResearchProject.school_id == actor.school_id, ResearchProject.leader_id == actor.id).order_by(ResearchProject.updated_at.desc()).limit(6)).all()
    mentor_research = db.scalars(select(ResearchProject).where(ResearchProject.school_id == actor.school_id, ResearchProject.mentor_id == actor.id).order_by(ResearchProject.updated_at.desc()).limit(8)).all()
    leader_projects = db.scalars(select(ImpactProject).where(ImpactProject.school_id == actor.school_id, ImpactProject.leader_id == actor.id).order_by(ImpactProject.updated_at.desc()).limit(6)).all()
    mentor_projects = db.scalars(select(ImpactProject).where(ImpactProject.school_id == actor.school_id, ImpactProject.mentor_id == actor.id).order_by(ImpactProject.updated_at.desc()).limit(6)).all()
    validated_clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.school_id == actor.school_id, ProblemCluster.status == "VALIDATED").order_by(ProblemCluster.updated_at.desc()).limit(8)).all()
    moderation_reports = db.scalars(select(ProblemReport).where(ProblemReport.school_id == actor.school_id, ProblemReport.status.in_(["MODERATION_REVIEW", "PRIVATE_REVIEW"])).order_by(ProblemReport.updated_at)).all()
    notifications = db.scalars(select(Notification).where(Notification.user_id == actor.id).order_by(Notification.created_at.desc()).limit(6)).all()
    updates = db.scalars(select(OfficialUpdate).where(OfficialUpdate.school_id == actor.school_id, OfficialUpdate.status != "PUBLISHED").order_by(OfficialUpdate.created_at.desc()).limit(6)).all()

    def task_item(task: ProjectTask) -> dict[str, Any]:
        return {"id": task.id, "title": task.title, "status": task.status, "priority": task.priority, "due_date": task.due_date, "href": f"/app/projects/{task.project_id}"}

    def research_item(item: ResearchProject) -> dict[str, Any]:
        return {"id": item.id, "title": item.title, "status": item.status, "href": f"/app/research/{item.id}", "cluster_id": item.cluster_id}

    def project_item(item: ImpactProject) -> dict[str, Any]:
        return {"id": item.id, "title": item.title, "status": item.status, "href": f"/app/projects/{item.id}", "cluster_id": item.cluster_id}

    def commitment_item(item: ResponseCommitment) -> dict[str, Any]:
        return commitment_dict(db, item, actor, include_updates=False)

    attention: list[dict[str, Any]] = []
    my_work: list[dict[str, Any]] = []
    role_sections: dict[str, Any] = {}
    primary_action = {"label": "Report a concern", "href": "/app/problems/new", "permission": "problem_report.create"}
    if selected_role == "STUDENT_CONTRIBUTOR":
        primary_action = {"label": "Report a concern", "href": "/app/problems/new", "permission": "problem_report.create"}
        my_work = [{"id": r.id, "title": r.title, "status": r.status, "href": f"/app/reports/{r.id}"} for r in own_reports] + [{"id": c.id, "title": c.title, "status": "FOLLOWING", "href": f"/app/problems/{c.id}"} for c in followed_clusters] + [commitment_item(item) for item in response_commitments]
        role_sections = {"my_recent_reports": [{"id": r.id, "title": r.title, "status": r.status, "href": f"/app/reports/{r.id}"} for r in own_reports], "followed_problems": [{"id": c.id, "title": c.title, "status": c.status, "href": f"/app/problems/{c.id}"} for c in followed_clusters], "response_commitments": [commitment_item(item) for item in response_commitments]}
        if not own_reports:
            attention.append({"id": "student-report", "title": "Start with a recurring concern", "detail": "Describe an observable issue affecting school life.", "href": "/app/problems/new"})
    elif selected_role == "STUDENT_PROJECT_LEADER":
        primary_action = {"label": "Continue active project" if leader_research or leader_projects else "Start from an approved problem", "href": f"/app/research/{leader_research[0].id}" if leader_research else "/app/problems" , "permission": "research.create"}
        my_work = [research_item(r) for r in leader_research] + [project_item(p) for p in leader_projects] + [task_item(t) for t in own_tasks] + [commitment_item(item) for item in response_commitments]
        attention = [{"id": r.id, "title": r.title, "detail": "Plan awaiting mentor review." if r.status == "MENTOR_REVIEW" else "Continue your research workspace.", "href": f"/app/research/{r.id}"} for r in leader_research if r.status in {"MENTOR_REVIEW", "CHANGES_REQUESTED", "DRAFT"}][:4]
        role_sections = {"research": [research_item(r) for r in leader_research], "projects": [project_item(p) for p in leader_projects], "tasks": [task_item(t) for t in own_tasks], "response_commitments": [commitment_item(item) for item in response_commitments]}
    elif selected_role == "MENTOR":
        primary_action = {"label": "Review next submission", "href": "/app/mentor/reviews", "permission": "mentor.review"}
        attention = [{"id": r.id, "title": r.title, "detail": "Research plan needs your decision.", "href": f"/app/research/{r.id}"} for r in mentor_research if r.status == "MENTOR_REVIEW"]
        attention += [{"id": item.id, "title": item.title, "detail": commitment_reminder(item)[1], "href": f"/app/problems/{item.cluster_id}"} for item in response_commitments if item.status not in RESPONSE_COMMITMENT_TERMINAL and commitment_reminder(item)]
        my_work = [research_item(r) for r in mentor_research] + [project_item(p) for p in mentor_projects] + [commitment_item(item) for item in response_commitments]
        role_sections = {"reviews_awaiting_attention": [research_item(r) for r in mentor_research if r.status == "MENTOR_REVIEW"], "assigned_research": [research_item(r) for r in mentor_research], "assigned_projects": [project_item(p) for p in mentor_projects], "response_commitments": [commitment_item(item) for item in response_commitments]}
    elif selected_role == "OSIS_REVIEWER":
        primary_action = {"label": "Review school priorities", "href": "/app/osis/priorities", "permission": "osis.priority_manage"}
        attention = [{"id": c.id, "title": c.title, "detail": "Validated problem ready for prioritization.", "href": f"/app/problems/{c.id}"} for c in validated_clusters]
        attention += [{"id": item.id, "title": item.title, "detail": commitment_reminder(item)[1], "href": f"/app/problems/{item.cluster_id}"} for item in response_commitments if item.status not in RESPONSE_COMMITMENT_TERMINAL and commitment_reminder(item)]
        my_work = [{"id": c.id, "title": c.title, "status": c.status, "href": f"/app/problems/{c.id}"} for c in validated_clusters] + [commitment_item(item) for item in response_commitments]
        role_sections = {"validated_problems": [{"id": c.id, "title": c.title, "status": c.status, "href": f"/app/problems/{c.id}"} for c in validated_clusters], "response_commitments": [commitment_item(item) for item in response_commitments], "official_updates": [{"id": u.id, "title": "Official update draft", "detail": u.message, "status": u.status, "href": f"/app/problems/{u.cluster_id}"} for u in updates]}
    elif selected_role == "MODERATOR":
        primary_action = {"label": "Review next report", "href": "/app/moderation/reports", "permission": "moderation.review"}
        attention = [{"id": r.id, "title": r.title, "detail": "Restricted review." if r.status == "PRIVATE_REVIEW" else "New report awaiting moderation.", "href": f"/app/moderation/reports/{r.id}"} for r in moderation_reports]
        my_work = attention + [commitment_item(item) for item in response_commitments]
        role_sections = {"new_reports": [a for a in attention if next((r.status for r in moderation_reports if r.id == a["id"]), "") == "MODERATION_REVIEW"], "restricted_reports": [a for a in attention if next((r.status for r in moderation_reports if r.id == a["id"]), "") == "PRIVATE_REVIEW"], "response_commitments": [commitment_item(item) for item in response_commitments]}
    elif selected_role == "ADMINISTRATOR":
        primary_action = {"label": "Invite SPI member", "href": "/app/admin/invitations", "permission": "admin.invitations.manage"}
        active_members = db.scalar(select(func.count()).select_from(User).where(User.school_id == actor.school_id, User.active.is_(True))) or 0
        deactivated_members = db.scalar(select(func.count()).select_from(User).where(User.school_id == actor.school_id, User.active.is_(False))) or 0
        pending_invitations = db.scalar(select(func.count()).select_from(Invitation).where(Invitation.school_id == actor.school_id, Invitation.status == "PENDING", Invitation.expires_at > datetime.utcnow())) or 0
        attention = [{"id": "admin-invites", "title": "Pending invitations", "detail": f"{pending_invitations} invitation(s) awaiting activation.", "href": "/app/admin/invitations"}, {"id": "admin-members", "title": "Membership oversight", "detail": f"{active_members} active and {deactivated_members} deactivated member(s).", "href": "/app/admin/members"}]
        attention += [{"id": item.id, "title": item.title, "detail": commitment_reminder(item)[1], "href": f"/app/problems/{item.cluster_id}"} for item in response_commitments if item.status not in RESPONSE_COMMITMENT_TERMINAL and commitment_reminder(item)]
        my_work = [commitment_item(item) for item in response_commitments]
        role_sections = {"members": {"active": active_members, "deactivated": deactivated_members}, "pending_invitations": pending_invitations, "response_commitments": [commitment_item(item) for item in response_commitments]}

    summary = {"my_open_reports": sum(1 for r in own_reports if r.status not in {"ARCHIVED", "MERGED"}), "followed_problems": len(followed_clusters), "incomplete_tasks": sum(1 for t in own_tasks if t.status != "COMPLETED") + sum(1 for item in response_commitments if item.status not in RESPONSE_COMMITMENT_TERMINAL), "attention_count": len(attention)}
    recent = [{"id": n.id, "title": n.title, "message": n.message, "href": "/app/notifications", "created_at": dt(n.created_at)} for n in notifications]
    db.commit()
    return {"viewer": {"id": actor.id, "display_name": actor.display_name, "school": {"id": school.id if school else actor.school_id, "name": school.name if school else "Pilar Impact Lab", "slug": school.slug if school else "pilar-impact-lab"}, "roles": [{"code": code, "label": ROLE_DETAILS.get(code, (code.replace("_", " ").title(), ""))[0]} for code in active_roles], "active_workspace": selected_role, "responsibility": role_description}, "primary_action": primary_action, "summary": summary, "attention_items": attention, "my_work": my_work, "recent_updates": recent, "role_sections": role_sections, "mode": app_mode(), "synthetic_data": app_mode() == "DEMO"}


@app.get(f"{API}/search")
def search(q: str = "", limit: int = 12, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Search only records the current member is already allowed to discover."""
    term = q.strip().lower()
    if len(term) < 2:
        return {"items": [], "query": q}
    limit = max(1, min(limit, 30))
    admin = has_active_role(db, actor, "ADMIN")
    reviewer = has_active_role(db, actor, "MODERATOR", "ADMIN")
    student = has_active_role(db, actor, "STUDENT", "STUDENT_LEADER")
    leader = has_active_role(db, actor, "STUDENT_LEADER")
    mentor = has_active_role(db, actor, "MENTOR")
    osis = has_active_role(db, actor, "OSIS")

    def matches(*values: Any) -> bool:
        return any(term in str(value or "").lower() for value in values)

    items: list[dict[str, Any]] = []

    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.school_id == actor.school_id)).all()
    for cluster in clusters:
        if osis and not reviewer and cluster.status != "VALIDATED":
            continue
        if matches(cluster.title, cluster.summary, cluster.category, cluster.scope):
            items.append({"id": cluster.id, "type": "problem", "label": "Problem", "title": cluster.title, "description": cluster.summary, "status": cluster.status, "href": f"/app/problems/{cluster.id}"})

    reports = db.scalars(select(ProblemReport).where(ProblemReport.school_id == actor.school_id, ProblemReport.author_id == actor.id if not reviewer else True)).all()
    for report in reports:
        if not reviewer and report.author_id != actor.id:
            continue
        if matches(report.title, report.description, report.category, report.scope):
            items.append({"id": report.id, "type": "report", "label": "My report" if report.author_id == actor.id else "Report", "title": report.title, "description": "Restricted report" if report.visibility == "PRIVATE_REVIEW" and not reviewer else report.description, "status": report.status, "href": f"/app/reports/{report.id}" if report.author_id == actor.id else f"/app/moderation/reports/{report.id}"})

    research_query = select(ResearchProject).where(ResearchProject.school_id == actor.school_id)
    for research in db.scalars(research_query).all():
        if not admin and not ((leader and research.leader_id == actor.id) or (mentor and research.mentor_id == actor.id)):
            continue
        if matches(research.title, research.status):
            items.append({"id": research.id, "type": "research", "label": "Research", "title": research.title, "description": "Research workspace", "status": research.status, "href": f"/app/research/{research.id}"})

    project_query = select(ImpactProject).where(ImpactProject.school_id == actor.school_id)
    for project in db.scalars(project_query).all():
        if not admin and not ((mentor and project.mentor_id == actor.id) or ((leader or student) and project.leader_id == actor.id)):
            continue
        if matches(project.title, project.status, project.intervention):
            items.append({"id": project.id, "type": "project", "label": "Impact project", "title": project.title, "description": "Impact workspace", "status": project.status, "href": f"/app/projects/{project.id}"})

    for task in db.scalars(select(ProjectTask).where(ProjectTask.owner_id == actor.id)).all():
        if matches(task.title, task.status, task.priority):
            items.append({"id": task.id, "type": "task", "label": "Task", "title": task.title, "description": "Assigned task", "status": task.status, "href": "/app/tasks"})

    items.sort(key=lambda item: (0 if item["title"].lower().startswith(term) else 1, item["title"].lower()))
    return {"items": items[:limit], "query": q}


@app.get(f"{API}/problem-reports")
def list_reports(actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    reports = db.scalars(select(ProblemReport).where(ProblemReport.school_id == actor.school_id).order_by(ProblemReport.updated_at.desc())).all()
    if not has_active_role(db, actor, "MODERATOR", "ADMIN"):
        reports = [r for r in reports if r.author_id == actor.id or r.status in {"PUBLISHED", "MERGED"}]
    return [report_dict(db, report, actor) for report in reports]


@app.get(f"{API}/problem-reports/mine")
def list_my_reports(actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    reports = db.scalars(select(ProblemReport).where(ProblemReport.school_id == actor.school_id, ProblemReport.author_id == actor.id).order_by(ProblemReport.updated_at.desc())).all()
    return [report_dict(db, report, actor) for report in reports]


@app.post(f"{API}/problem-reports", dependencies=[Depends(require_csrf)])
def create_report(payload: ProblemCreate, actor: User = Depends(require_roles("STUDENT", "STUDENT_LEADER", "MENTOR", "MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = ProblemReport(id=new_id(), school_id=actor.school_id, author_id=actor.id, **payload.model_dump())
    db.add(report)
    audit(db, actor, "PROBLEM_DRAFT_CREATED", "PROBLEM_REPORT", report.id)
    db.commit()
    return {"report": report_dict(db, report, actor), "ai": ai_framing(report.title, report.description)}


@app.patch(f"{API}/problem-reports/{{report_id}}", dependencies=[Depends(require_csrf)])
def update_report(report_id: str, payload: ProblemUpdate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report:
        raise HTTPException(404, "Report not found.")
    require_same_school(actor, report.school_id)
    reviewer = has_active_role(db, actor, "MODERATOR", "ADMIN")
    if report.author_id != actor.id and not reviewer:
        raise HTTPException(403, "Only the author or a moderator can edit this report.")
    if report.status not in {"DRAFT", "CHANGES_REQUESTED"} and not reviewer:
        raise HTTPException(409, "Submitted reports are not editable by students.")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(report, key, value)
    audit(db, actor, "PROBLEM_DRAFT_UPDATED", "PROBLEM_REPORT", report.id)
    db.commit()
    return report_dict(db, report, actor)


@app.get(f"{API}/problem-reports/{{report_id}}")
def get_report(report_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report:
        raise HTTPException(404, "Report not found.")
    require_same_school(actor, report.school_id)
    if report.status == "PRIVATE_REVIEW" and actor.id != report.author_id and not has_active_role(db, actor, "MODERATOR", "ADMIN"):
        raise HTTPException(404, "Report not found.")
    return report_dict(db, report, actor)


@app.post(f"{API}/problem-reports/{{report_id}}/follow-up-evidence", dependencies=[Depends(require_csrf)])
def add_report_follow_up_evidence(report_id: str, payload: EvidenceCreate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report or report.school_id != actor.school_id:
        raise HTTPException(status_code=404, detail="Report not found.")
    reviewer = has_active_role(db, actor, "MODERATOR", "ADMIN")
    if report.author_id != actor.id and not reviewer:
        raise HTTPException(status_code=403, detail="Only the report author or a designated reviewer can add follow-up evidence.")
    if report.status in {"ARCHIVED", "WITHDRAWN", "MERGED"}:
        raise HTTPException(status_code=409, detail="Follow-up evidence cannot be added to this report state.")
    evidence = Evidence(id=new_id(), school_id=actor.school_id, author_id=actor.id, report_id=report.id, cluster_id=report.cluster_id, **payload.model_dump())
    db.add(evidence)
    audit(db, actor, "REPORT_FOLLOW_UP_EVIDENCE_ADDED", "PROBLEM_REPORT", report.id, {"evidence_id": evidence.id, "visibility": evidence.visibility})
    db.commit()
    return report_dict(db, report, actor)


@app.post(f"{API}/problem-reports/{{report_id}}/request-correction", dependencies=[Depends(require_csrf)])
def request_report_correction(report_id: str, payload: DecisionRequest, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report or report.school_id != actor.school_id:
        raise HTTPException(status_code=404, detail="Report not found.")
    if report.author_id != actor.id:
        raise HTTPException(status_code=403, detail="Only the report author can request a correction.")
    if report.status not in {"MODERATION_REVIEW", "PRIVATE_REVIEW"}:
        raise HTTPException(status_code=409, detail="A correction can only be requested before publication.")
    transition(db, actor, report, "PROBLEM_REPORT", "CHANGES_REQUESTED", PROBLEM_TRANSITIONS, payload.reason)
    audit(db, actor, "REPORT_CORRECTION_REQUESTED", "PROBLEM_REPORT", report.id, {"reason_recorded": True})
    for moderator in db.scalars(select(User).where(User.school_id == actor.school_id, User.role.in_(["MODERATOR", "ADMIN"]), User.active.is_(True))).all():
        notify(db, moderator.id, "Report correction requested", f"The author requested a correction for: {report.title}")
    db.commit()
    return report_dict(db, report, actor)


@app.post(f"{API}/problem-reports/{{report_id}}/withdraw", dependencies=[Depends(require_csrf)])
def withdraw_report(report_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report or report.school_id != actor.school_id:
        raise HTTPException(status_code=404, detail="Report not found.")
    if report.author_id != actor.id:
        raise HTTPException(status_code=403, detail="Only the report author can withdraw this report.")
    if report.status not in {"DRAFT", "MODERATION_REVIEW", "PRIVATE_REVIEW", "CHANGES_REQUESTED"}:
        raise HTTPException(status_code=409, detail="This report can no longer be withdrawn.")
    transition(db, actor, report, "PROBLEM_REPORT", "WITHDRAWN", PROBLEM_TRANSITIONS, "Author withdrew the report before publication.")
    audit(db, actor, "REPORT_WITHDRAWN", "PROBLEM_REPORT", report.id)
    db.commit()
    return report_dict(db, report, actor)


@app.post(f"{API}/problem-reports/{{report_id}}/submit", dependencies=[Depends(require_csrf)])
def submit_report(report_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report:
        raise HTTPException(404, "Report not found.")
    require_same_school(actor, report.school_id)
    if report.author_id != actor.id and not has_active_role(db, actor, "MODERATOR", "ADMIN"):
        raise HTTPException(403, "Only the author can submit this report.")
    if report.status != "DRAFT":
        raise HTTPException(409, "Only a draft can be submitted.")
    detected = sensitivity_reason(report.title, report.description)
    target = "PRIVATE_REVIEW" if report.visibility == "PRIVATE_REVIEW" or detected else "MODERATION_REVIEW"
    report.sensitivity_reason = detected
    transition(db, actor, report, "PROBLEM_REPORT", target, PROBLEM_TRANSITIONS, "Student submitted report")
    for moderator in db.scalars(select(User).where(User.school_id == actor.school_id, User.role.in_(["MODERATOR", "ADMIN"]), User.active.is_(True))).all():
        notify(db, moderator.id, "New moderation item", f"A report is ready for {target.replace('_', ' ').lower()}.")
    db.commit()
    return {"report": report_dict(db, report, actor), "ai": ai_framing(report.title, report.description), "safety_route": target == "PRIVATE_REVIEW"}


@app.get(f"{API}/problem-clusters")
@app.get(f"{API}/problems")
def list_clusters(search: str = "", category: str = "", status: str = "", sort: str = "updated", needs_response: bool = False, stale: bool = False, priority: str = "", actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    query = select(ProblemCluster).where(ProblemCluster.school_id == actor.school_id)
    if search.strip():
        term = f"%{search.strip()}%"
        query = query.where(ProblemCluster.title.ilike(term) | ProblemCluster.summary.ilike(term))
    if category.strip():
        query = query.where(ProblemCluster.category == category.upper())
    if status.strip():
        query = query.where(ProblemCluster.status == status.upper())
    if has_active_role(db, actor, "OSIS") and not has_active_role(db, actor, "MODERATOR", "ADMIN"):
        query = query.where(ProblemCluster.status == "VALIDATED")
    order_column = ProblemCluster.title if sort == "title" else ProblemCluster.created_at if sort == "created" else ProblemCluster.updated_at
    clusters = db.scalars(query.order_by(order_column.desc())).all()
    rows = [cluster_dict(db, cluster, actor) for cluster in clusters]
    if needs_response:
        rows = [row for row in rows if row["needs_response"]]
    if stale:
        rows = [row for row in rows if row["response_loop"].get("is_stale")]
    if priority.strip():
        rows = [row for row in rows if row.get("priority") == priority.upper()]
    if sort == "priority":
        order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, None: 4}
        rows.sort(key=lambda row: order.get(row.get("priority"), 5))
    return rows


@app.get(f"{API}/problem-clusters/{{cluster_id}}")
@app.get(f"{API}/problems/{{cluster_id}}")
def get_cluster(cluster_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    if has_active_role(db, actor, "OSIS") and not has_active_role(db, actor, "MODERATOR", "ADMIN") and cluster.status != "VALIDATED":
        raise HTTPException(404, "Problem cluster not found.")
    return cluster_dict(db, cluster, actor)


@app.get(f"{API}/problem-clusters/{{cluster_id}}/timeline")
@app.get(f"{API}/problems/{{cluster_id}}/timeline")
def problem_timeline(cluster_id: str, actor: User = Depends(require_permissions("problem.read_public_school")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster or cluster.school_id != actor.school_id:
        raise HTTPException(status_code=404, detail="Problem cluster not found.")
    if has_active_role(db, actor, "OSIS") and not has_active_role(db, actor, "MODERATOR", "ADMIN") and cluster.status != "VALIDATED":
        raise HTTPException(status_code=404, detail="Problem cluster not found.")
    return {"cluster_id": cluster.id, "items": cluster_timeline(db, cluster, actor)}


@app.get(f"{API}/problem-clusters/{{cluster_id}}/work")
@app.get(f"{API}/problems/{{cluster_id}}/work")
def problem_work(cluster_id: str, actor: User = Depends(require_permissions("problem.read_public_school")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster or cluster.school_id != actor.school_id:
        raise HTTPException(status_code=404, detail="Problem cluster not found.")
    if has_active_role(db, actor, "OSIS") and not has_active_role(db, actor, "MODERATOR", "ADMIN") and cluster.status != "VALIDATED":
        raise HTTPException(status_code=404, detail="Problem cluster not found.")
    manager = has_active_role(db, actor, "MENTOR", "OSIS", "ADMIN")
    commitments = db.scalars(select(ResponseCommitment).where(ResponseCommitment.cluster_id == cluster.id).order_by(ResponseCommitment.updated_at.desc())).all()
    commitments = [item for item in commitments if item.visibility == "SCHOOL" or commitment_scope(db, actor, item)[0]]
    projects = db.scalars(select(ImpactProject).where(ImpactProject.cluster_id == cluster.id, ImpactProject.school_id == actor.school_id)).all()
    project_ids = {project.id for project in projects}
    tasks = db.scalars(select(ProjectTask).where(ProjectTask.project_id.in_(project_ids))).all() if project_ids else []
    visible_tasks = []
    for task in tasks:
        project = next((item for item in projects if item.id == task.project_id), None)
        if not project:
            continue
        if manager or task.owner_id == actor.id or actor.id in {project.leader_id, project.mentor_id}:
            visible_tasks.append({"id": task.id, "type": "PROJECT_TASK", "title": task.title, "status": task.status, "priority": task.priority, "due_date": task.due_date, "owner_id": task.owner_id, "project_id": task.project_id, "cluster_id": cluster.id, "cluster_title": cluster.title, "href": f"/app/projects/{task.project_id}"})
    return {"cluster_id": cluster.id, "commitments": [commitment_dict(db, item, actor) for item in commitments], "project_tasks": visible_tasks}


@app.get(f"{API}/work")
def unified_work(status_filter: str = "", kind: str = "", stale: bool = False, actor: User = Depends(require_permissions("response_commitment.read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    manager = has_active_role(db, actor, "MENTOR", "OSIS", "ADMIN")
    commitment_query = select(ResponseCommitment).where(ResponseCommitment.school_id == actor.school_id)
    if not manager:
        commitment_query = commitment_query.where(ResponseCommitment.owner_id == actor.id)
    commitments = db.scalars(commitment_query.order_by(ResponseCommitment.due_date, ResponseCommitment.title)).all()
    ensure_commitment_reminders(db, actor, commitments)
    tasks = []
    if "task.read_assigned" in active_permissions(db, actor):
        tasks = db.scalars(select(ProjectTask).join(ImpactProject, ImpactProject.id == ProjectTask.project_id).where(ImpactProject.school_id == actor.school_id, ProjectTask.owner_id == actor.id).order_by(ProjectTask.due_date, ProjectTask.title)).all()
    project_map = {project.id: project for project in db.scalars(select(ImpactProject).where(ImpactProject.school_id == actor.school_id, ImpactProject.id.in_({task.project_id for task in tasks}))).all()}
    items: list[dict[str, Any]] = []
    for item in commitments:
        row = commitment_dict(db, item, actor)
        if status_filter.strip() and item.status != status_filter.upper():
            continue
        if stale and not row["is_stale"]:
            continue
        if kind.strip() and kind.upper() not in {"RESPONSE_COMMITMENT", "COMMITMENT"}:
            continue
        items.append(row)
    for task in tasks:
        if status_filter.strip() and task.status != status_filter.upper():
            continue
        if kind.strip() and kind.upper() not in {"PROJECT_TASK", "TASK"}:
            continue
        due = parse_day(task.due_date, "due_date")
        project = project_map.get(task.project_id)
        items.append({"id": task.id, "type": "PROJECT_TASK", "title": task.title, "status": task.status, "priority": task.priority, "due_date": task.due_date, "owner_id": task.owner_id, "project_id": task.project_id, "cluster_id": project.cluster_id if project else None, "cluster_title": db.get(ProblemCluster, project.cluster_id).title if project and db.get(ProblemCluster, project.cluster_id) else None, "is_overdue": bool(due and due < date.today() and task.status != "COMPLETED"), "is_stale": False, "reminder_state": "OVERDUE" if due and due < date.today() and task.status != "COMPLETED" else None, "href": f"/app/projects/{task.project_id}"})
    items.sort(key=lambda item: (item.get("due_date") or "9999-12-31", item.get("title") or ""))
    if commitments:
        db.commit()
    return {"items": items, "summary": {"total": len(items), "response_commitments": sum(1 for item in items if item["type"] == "RESPONSE_COMMITMENT"), "project_tasks": sum(1 for item in items if item["type"] == "PROJECT_TASK"), "overdue": sum(1 for item in items if item.get("is_overdue")), "stale": sum(1 for item in items if item.get("is_stale"))}, "manager_view": manager}


@app.post(f"{API}/problem-clusters/{{cluster_id}}/signals", dependencies=[Depends(require_csrf)])
@app.post(f"{API}/problems/{{cluster_id}}/signals", dependencies=[Depends(require_csrf)])
def add_signal(cluster_id: str, payload: SignalCreate, actor: User = Depends(require_permissions("problem.signal")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    existing = db.scalar(select(ProblemSignal).where(ProblemSignal.cluster_id == cluster_id, ProblemSignal.user_id == actor.id, ProblemSignal.signal_type == payload.signal_type))
    if existing:
        raise HTTPException(409, "You have already added this signal.")
    db.add(ProblemSignal(id=new_id(), cluster_id=cluster_id, user_id=actor.id, signal_type=payload.signal_type))
    audit(db, actor, "SIGNAL_ADDED", "PROBLEM_CLUSTER", cluster_id, {"signal_type": payload.signal_type})
    db.commit()
    return cluster_dict(db, cluster, actor)


@app.delete(f"{API}/problem-clusters/{{cluster_id}}/signals/{{signal_type}}", dependencies=[Depends(require_csrf)])
@app.delete(f"{API}/problems/{{cluster_id}}/signals/{{signal_type}}", dependencies=[Depends(require_csrf)])
def delete_signal(cluster_id: str, signal_type: str, actor: User = Depends(require_permissions("problem.signal")), db: Session = Depends(get_db)) -> dict[str, Any]:
    signal = db.scalar(select(ProblemSignal).where(ProblemSignal.cluster_id == cluster_id, ProblemSignal.user_id == actor.id, ProblemSignal.signal_type == signal_type))
    if signal:
        db.delete(signal)
        audit(db, actor, "SIGNAL_REMOVED", "PROBLEM_CLUSTER", cluster_id, {"signal_type": signal_type})
        db.commit()
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    return cluster_dict(db, cluster, actor)


@app.post(f"{API}/problem-clusters/{{cluster_id}}/follow", dependencies=[Depends(require_csrf)])
@app.post(f"{API}/problems/{{cluster_id}}/follow", dependencies=[Depends(require_csrf)])
def follow_problem(cluster_id: str, actor: User = Depends(require_permissions("problem.follow")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    existing = db.scalar(select(ProblemFollow).where(ProblemFollow.cluster_id == cluster_id, ProblemFollow.user_id == actor.id))
    if not existing:
        db.add(ProblemFollow(id=new_id(), cluster_id=cluster_id, user_id=actor.id))
        audit(db, actor, "PROBLEM_FOLLOWED", "PROBLEM_CLUSTER", cluster_id)
        db.commit()
    return cluster_dict(db, cluster, actor)


@app.delete(f"{API}/problem-clusters/{{cluster_id}}/follow", dependencies=[Depends(require_csrf)])
@app.delete(f"{API}/problems/{{cluster_id}}/follow", dependencies=[Depends(require_csrf)])
def unfollow_problem(cluster_id: str, actor: User = Depends(require_permissions("problem.follow")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    existing = db.scalar(select(ProblemFollow).where(ProblemFollow.cluster_id == cluster_id, ProblemFollow.user_id == actor.id))
    if existing:
        db.delete(existing)
        audit(db, actor, "PROBLEM_UNFOLLOWED", "PROBLEM_CLUSTER", cluster_id)
        db.commit()
    return cluster_dict(db, cluster, actor)


@app.post(f"{API}/problem-clusters/{{cluster_id}}/evidence", dependencies=[Depends(require_csrf)])
def add_evidence(cluster_id: str, payload: EvidenceCreate, actor: User = Depends(require_permissions("problem_report.create")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    evidence = Evidence(id=new_id(), school_id=actor.school_id, author_id=actor.id, cluster_id=cluster_id, **payload.model_dump())
    db.add(evidence)
    audit(db, actor, "EVIDENCE_ADDED", "EVIDENCE", evidence.id, {"cluster_id": cluster_id, "type": payload.evidence_type})
    db.commit()
    return cluster_dict(db, cluster, actor)


@app.get(f"{API}/moderation/queue")
@app.get(f"{API}/moderation/reports")
def moderation_queue(actor: User = Depends(require_roles("MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    reports = db.scalars(select(ProblemReport).where(ProblemReport.school_id == actor.school_id, ProblemReport.status.in_(["PRIVATE_REVIEW", "MODERATION_REVIEW"])).order_by(ProblemReport.created_at)).all()
    return {"private": [report_dict(db, r, actor) for r in reports if r.status == "PRIVATE_REVIEW"], "visibility": [report_dict(db, r, actor) for r in reports if r.status == "MODERATION_REVIEW"], "duplicate_candidates": [{"report_id": r.id, "candidates": []} for r in reports]}


@app.get(f"{API}/moderation/reports/{{report_id}}")
def moderation_report(report_id: str, actor: User = Depends(require_permissions("moderation.review")), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report or report.school_id != actor.school_id or report.status not in {"MODERATION_REVIEW", "PRIVATE_REVIEW", "CHANGES_REQUESTED"}:
        raise HTTPException(404, "Moderation report not found.")
    return report_dict(db, report, actor)


@app.post(f"{API}/moderation/problem-reports/{{report_id}}/visibility-decision", dependencies=[Depends(require_csrf)])
@app.post(f"{API}/moderation/reports/{{report_id}}/decision", dependencies=[Depends(require_csrf)])
def visibility_decision(report_id: str, payload: DecisionRequest, actor: User = Depends(require_roles("MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report:
        raise HTTPException(404, "Report not found.")
    require_same_school(actor, report.school_id)
    decision = payload.decision.upper()
    if decision in {"PUBLISH", "APPROVE_FOR_CLUSTERING"}:
        if not report.cluster_id:
            cluster = ProblemCluster(id=new_id(), school_id=actor.school_id, title=report.title, summary=report.description, category=report.category, scope=report.scope, status="GATHERING_EVIDENCE")
            db.add(cluster)
            db.flush()
            report.cluster_id = cluster.id
        target = "PUBLISHED"
    elif decision in {"KEEP_PRIVATE", "ROUTE_TO_RESTRICTED_REVIEW"}:
        target = "PRIVATE_REVIEW"
    elif decision == "RETURN_FOR_CLARIFICATION":
        target = "CHANGES_REQUESTED"
    elif decision == "ARCHIVE":
        target = "ARCHIVED"
    else:
        raise HTTPException(422, "Choose approve, return, restrict, or archive.")
    if report.status != target:
        transition(db, actor, report, "PROBLEM_REPORT", target, PROBLEM_TRANSITIONS, payload.reason)
    audit(db, actor, "VISIBILITY_DECISION", "PROBLEM_REPORT", report.id, {"decision": decision})
    notify(db, report.author_id, "Report status updated", f"Your problem report is now {target.replace('_', ' ').lower()}.")
    db.commit()
    return report_dict(db, report, actor)


@app.post(f"{API}/moderation/problem-reports/{{report_id}}/merge", dependencies=[Depends(require_csrf)])
def merge_report(report_id: str, payload: MergeRequest, actor: User = Depends(require_roles("MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    cluster = db.get(ProblemCluster, payload.cluster_id)
    if not report or not cluster:
        raise HTTPException(404, "Report or cluster not found.")
    require_same_school(actor, report.school_id)
    require_same_school(actor, cluster.school_id)
    report.cluster_id = cluster.id
    if report.status != "MERGED":
        if report.status in PROBLEM_TRANSITIONS and "MERGED" in PROBLEM_TRANSITIONS[report.status]:
            transition(db, actor, report, "PROBLEM_REPORT", "MERGED", PROBLEM_TRANSITIONS, payload.reason)
        else:
            report.status = "MERGED"
    audit(db, actor, "REPORT_MERGED", "PROBLEM_REPORT", report.id, {"cluster_id": cluster.id})
    db.commit()
    return cluster_dict(db, cluster, actor)


@app.post(f"{API}/moderation/problem-reports/{{report_id}}/unmerge", dependencies=[Depends(require_csrf)])
def unmerge_report(report_id: str, payload: DecisionRequest, actor: User = Depends(require_roles("MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report:
        raise HTTPException(404, "Report not found.")
    require_same_school(actor, report.school_id)
    report.cluster_id = None
    if report.status == "MERGED":
        report.status = "PUBLISHED"
    audit(db, actor, "REPORT_UNMERGED", "PROBLEM_REPORT", report.id, {"reason": payload.reason})
    db.commit()
    return report_dict(db, report, actor)


@app.post(f"{API}/problem-clusters/{{cluster_id}}/official-updates", dependencies=[Depends(require_csrf)])
def official_update(cluster_id: str, payload: OfficialUpdateCreate, actor: User = Depends(require_permissions("osis.official_update_manage")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    update = OfficialUpdate(id=new_id(), school_id=actor.school_id, cluster_id=cluster_id, author_id=actor.id, status=payload.status, message=payload.message)
    db.add(update)
    cluster.updated_at = datetime.utcnow()
    for report in db.scalars(select(ProblemReport).where(ProblemReport.cluster_id == cluster_id)).all():
        notify(db, report.author_id, "Official update", payload.message)
    if payload.status.upper() not in {"DRAFT", "PUBLISHED"}:
        raise HTTPException(422, "Official updates must be drafts or published updates.")
    audit(db, actor, "OFFICIAL_UPDATE_CREATED", "OFFICIAL_UPDATE", update.id, {"status": payload.status.upper(), "cluster_id": cluster_id})
    db.commit()
    return cluster_dict(db, cluster, actor)


@app.get(f"{API}/osis/priorities")
def osis_priorities(actor: User = Depends(require_permissions("osis.review")), db: Session = Depends(get_db)) -> dict[str, Any]:
    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.school_id == actor.school_id, ProblemCluster.status == "VALIDATED").order_by(ProblemCluster.updated_at.desc())).all()
    return {"items": [cluster_dict(db, cluster, actor) for cluster in clusters], "non_sensitive_only": True}


@app.post(f"{API}/osis/problems/{{cluster_id}}/priority", dependencies=[Depends(require_csrf)])
def set_osis_priority(cluster_id: str, payload: PriorityRequest, actor: User = Depends(require_permissions("osis.priority_manage")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster or cluster.school_id != actor.school_id or cluster.status != "VALIDATED":
        raise HTTPException(404, "Validated problem not found.")
    priority = db.scalar(select(ProblemPriority).where(ProblemPriority.cluster_id == cluster_id, ProblemPriority.school_id == actor.school_id))
    if not priority:
        priority = ProblemPriority(id=new_id(), cluster_id=cluster_id, school_id=actor.school_id, assigned_by=actor.id, priority=payload.priority, rationale=payload.rationale)
        db.add(priority)
    else:
        priority.priority = payload.priority
        priority.rationale = payload.rationale
        priority.assigned_by = actor.id
    cluster.updated_at = datetime.utcnow()
    audit(db, actor, "OSIS_PRIORITY_SET", "PROBLEM_CLUSTER", cluster_id, {"priority": payload.priority})
    db.commit()
    return cluster_dict(db, cluster, actor)


def get_commitment_or_404(db: Session, actor: User, commitment_id: str) -> ResponseCommitment:
    commitment = db.get(ResponseCommitment, commitment_id)
    if not commitment or commitment.school_id != actor.school_id:
        raise HTTPException(status_code=404, detail="Response commitment not found.")
    cluster = db.get(ProblemCluster, commitment.cluster_id)
    if not cluster or cluster.school_id != actor.school_id or cluster.status not in RESPONSE_VISIBLE_CLUSTER_STATES:
        raise HTTPException(status_code=404, detail="Response commitment not found.")
    return commitment


@app.post(f"{API}/problem-clusters/{{cluster_id}}/priority-assessment", dependencies=[Depends(require_csrf)])
@app.post(f"{API}/problems/{{cluster_id}}/priority-assessment", dependencies=[Depends(require_csrf)])
def assess_problem_priority(cluster_id: str, payload: PriorityAssessmentRequest, actor: User = Depends(require_permissions("problem.priority_assess")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster or cluster.school_id != actor.school_id or cluster.status != "VALIDATED":
        raise HTTPException(status_code=404, detail="Validated problem not found.")
    parse_day(payload.review_date, "review_date")
    priority = db.scalar(select(ProblemPriority).where(ProblemPriority.cluster_id == cluster_id, ProblemPriority.school_id == actor.school_id))
    if not priority:
        priority = ProblemPriority(id=new_id(), cluster_id=cluster_id, school_id=actor.school_id, assigned_by=actor.id, priority=payload.priority, rationale=payload.rationale)
        db.add(priority)
    priority.priority = payload.priority
    priority.rationale = payload.rationale
    priority.evidence_strength = payload.evidence_strength
    priority.urgency_score = payload.urgency_score
    priority.reach_score = payload.reach_score
    priority.feasibility_score = payload.feasibility_score
    priority.reviewed_by = actor.id
    priority.reviewed_at = datetime.utcnow()
    priority.review_date = payload.review_date
    priority.assigned_by = actor.id
    cluster.priority_rationale = payload.rationale
    cluster.updated_at = datetime.utcnow()
    audit(db, actor, "PROBLEM_PRIORITY_ASSESSED", "PROBLEM_CLUSTER", cluster.id, {"priority": payload.priority, "evidence_strength": payload.evidence_strength, "urgency_score": payload.urgency_score, "reach_score": payload.reach_score, "feasibility_score": payload.feasibility_score})
    db.commit()
    return cluster_dict(db, cluster, actor)


@app.get(f"{API}/response-commitments/{{commitment_id}}")
def get_response_commitment(commitment_id: str, actor: User = Depends(require_permissions("response_commitment.read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    commitment = get_commitment_or_404(db, actor, commitment_id)
    if commitment.visibility == "TEAM" and not commitment_scope(db, actor, commitment)[0]:
        raise HTTPException(status_code=404, detail="Response commitment not found.")
    return commitment_dict(db, commitment, actor)


@app.post(f"{API}/response-commitments", dependencies=[Depends(require_csrf)])
def create_response_commitment(payload: ResponseCommitmentCreate, actor: User = Depends(require_permissions("response_commitment.create")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, payload.cluster_id)
    if not cluster or cluster.school_id != actor.school_id or cluster.status not in RESPONSE_VISIBLE_CLUSTER_STATES:
        raise HTTPException(status_code=404, detail="A validated problem is required before creating a response commitment.")
    if not payload.due_date and not payload.next_update_date:
        raise HTTPException(status_code=422, detail="Set a due date or next-update date so the commitment can be followed through.")
    parse_day(payload.due_date, "due_date")
    parse_day(payload.next_update_date, "next_update_date")
    validate_commitment_links(db, actor, payload.cluster_id, payload.research_id, payload.project_id)
    owner_role, owner = validate_commitment_owner(db, actor, payload.owner_role, payload.owner_id)
    item = ResponseCommitment(id=new_id(), school_id=actor.school_id, cluster_id=payload.cluster_id, research_id=payload.research_id, project_id=payload.project_id, title=payload.title, intended_outcome=payload.intended_outcome, owner_role=owner_role, owner_id=owner.id if owner else None, assigned_by=actor.id, priority=payload.priority, due_date=payload.due_date, next_update_date=payload.next_update_date or payload.due_date, visibility=payload.visibility)
    db.add(item)
    audit(db, actor, "RESPONSE_COMMITMENT_CREATED", "RESPONSE_COMMITMENT", item.id, {"cluster_id": item.cluster_id, "owner_role": item.owner_role, "owner_id": item.owner_id, "priority": item.priority})
    if owner and owner.id != actor.id:
        notify(db, owner.id, "You own a response commitment", f"{item.title} needs an update by {item.next_update_date or item.due_date or 'the agreed date'}.")
    db.commit()
    return commitment_dict(db, item, actor)


@app.patch(f"{API}/response-commitments/{{commitment_id}}", dependencies=[Depends(require_csrf)])
def patch_response_commitment(commitment_id: str, payload: ResponseCommitmentPatch, actor: User = Depends(require_permissions("response_commitment.manage_assigned")), db: Session = Depends(get_db)) -> dict[str, Any]:
    item = get_commitment_or_404(db, actor, commitment_id)
    can_manage, manager = commitment_scope(db, actor, item)
    if not can_manage:
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Only the commitment owner or an accountable reviewer can update this commitment."})
    changes = payload.model_dump(exclude_unset=True)
    next_status = changes.get("status")
    previous_status = item.status
    if next_status and next_status != item.status:
        if next_status == "COMPLETED" and not (str(changes.get("completion_note", item.completion_note) or "").strip() or str(changes.get("evidence_reference", item.evidence_reference) or "").strip()):
            raise HTTPException(status_code=422, detail="A completed commitment needs a completion note or evidence reference.")
        if next_status == "NOT_NOW" and not (changes.get("next_update_date", item.next_update_date) and (str(changes.get("reason", "") or "").strip() or str(changes.get("blocker", item.blocker) or "").strip() or str(changes.get("completion_note", item.completion_note) or "").strip())):
            raise HTTPException(status_code=422, detail="A not-now decision needs a reason and a next-update date.")
        if next_status in {"DECLINED", "BLOCKED"} and not (str(changes.get("reason", "") or "").strip() or str(changes.get("blocker", item.blocker) or "").strip()):
            raise HTTPException(status_code=422, detail="Add a reason for declining or blocking this commitment.")
        transition(db, actor, item, "RESPONSE_COMMITMENT", next_status, RESPONSE_COMMITMENT_TRANSITIONS, str(changes.get("reason", "") or changes.get("blocker", "") or "").strip())
        if next_status == "COMPLETED":
            item.completed_at = datetime.utcnow()
        elif item.status != "COMPLETED":
            item.completed_at = None
    if "due_date" in changes:
        parse_day(changes["due_date"], "due_date")
    if "next_update_date" in changes:
        parse_day(changes["next_update_date"], "next_update_date")
    if "owner_role" in changes or "owner_id" in changes:
        owner_role, owner = validate_commitment_owner(db, actor, changes.get("owner_role", item.owner_role), changes.get("owner_id", item.owner_id))
        if item.owner_id != (owner.id if owner else None):
            audit(db, actor, "RESPONSE_COMMITMENT_OWNER_CHANGED", "RESPONSE_COMMITMENT", item.id, {"from_owner_id": item.owner_id, "to_owner_id": owner.id if owner else None, "owner_role": owner_role})
            item.owner_id = owner.id if owner else None
        item.owner_role = owner_role
    for field in ("title", "intended_outcome", "priority", "due_date", "next_update_date", "blocker", "completion_note", "evidence_reference", "visibility"):
        if field in changes:
            setattr(item, field, changes[field])
    item.updated_at = datetime.utcnow()
    audit(db, actor, "RESPONSE_COMMITMENT_UPDATED", "RESPONSE_COMMITMENT", item.id, {"fields": sorted(field for field in changes if field != "reason")})
    if next_status and next_status != previous_status and item.owner_id and item.owner_id != actor.id:
        notify(db, item.owner_id, "Response commitment updated", f"{item.title} is now {item.status.replace('_', ' ').lower()}.")
    db.commit()
    return commitment_dict(db, item, actor)


@app.post(f"{API}/response-commitments/{{commitment_id}}/updates", dependencies=[Depends(require_csrf)])
def create_response_commitment_update(commitment_id: str, payload: ResponseCommitmentUpdateCreate, actor: User = Depends(require_permissions("response_commitment.manage_assigned")), db: Session = Depends(get_db)) -> dict[str, Any]:
    item = get_commitment_or_404(db, actor, commitment_id)
    can_manage, _ = commitment_scope(db, actor, item)
    if not can_manage:
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Only the commitment owner or an accountable reviewer can add an update."})
    update = ResponseCommitmentUpdate(id=new_id(), school_id=actor.school_id, commitment_id=item.id, author_id=actor.id, kind=payload.kind, message=payload.message, visibility=payload.visibility)
    db.add(update)
    item.updated_at = datetime.utcnow()
    audit(db, actor, "RESPONSE_COMMITMENT_UPDATE_ADDED", "RESPONSE_COMMITMENT", item.id, {"kind": payload.kind, "visibility": payload.visibility})
    if item.owner_id and item.owner_id != actor.id:
        notify(db, item.owner_id, "Response commitment update", payload.message)
    db.commit()
    return commitment_dict(db, item, actor)


@app.post(f"{API}/response-commitments/{{commitment_id}}/transfer", dependencies=[Depends(require_csrf)])
def transfer_response_commitment(commitment_id: str, payload: ResponseCommitmentTransfer, actor: User = Depends(require_permissions("response_commitment.manage")), db: Session = Depends(get_db)) -> dict[str, Any]:
    item = get_commitment_or_404(db, actor, commitment_id)
    owner_role, owner = validate_commitment_owner(db, actor, payload.owner_role, payload.owner_id)
    previous_owner = item.owner_id
    item.owner_role = owner_role
    item.owner_id = owner.id if owner else None
    item.assigned_by = actor.id
    item.updated_at = datetime.utcnow()
    audit(db, actor, "RESPONSE_COMMITMENT_TRANSFERRED", "RESPONSE_COMMITMENT", item.id, {"from_owner_id": previous_owner, "to_owner_id": item.owner_id, "owner_role": owner_role, "reason": payload.reason})
    if owner and owner.id != actor.id:
        notify(db, owner.id, "Response commitment assigned to you", f"{item.title} needs an update by {item.next_update_date or item.due_date or 'the agreed date'}.")
    db.commit()
    return commitment_dict(db, item, actor)


@app.post(f"{API}/response-commitments/{{commitment_id}}/complete", dependencies=[Depends(require_csrf)])
def complete_response_commitment(commitment_id: str, payload: ResponseCommitmentComplete, actor: User = Depends(require_permissions("response_commitment.manage_assigned")), db: Session = Depends(get_db)) -> dict[str, Any]:
    item = get_commitment_or_404(db, actor, commitment_id)
    can_manage, _ = commitment_scope(db, actor, item)
    if not can_manage:
        raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "Only the commitment owner or an accountable reviewer can complete this commitment."})
    transition(db, actor, item, "RESPONSE_COMMITMENT", "COMPLETED", RESPONSE_COMMITMENT_TRANSITIONS, "Completion recorded by owner.")
    item.completion_note = payload.completion_note
    item.evidence_reference = payload.evidence_reference
    item.completed_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()
    audit(db, actor, "RESPONSE_COMMITMENT_COMPLETED", "RESPONSE_COMMITMENT", item.id, {"has_evidence_reference": bool(payload.evidence_reference.strip())})
    db.commit()
    return commitment_dict(db, item, actor)


@app.post(f"{API}/research-projects", dependencies=[Depends(require_csrf)])
def create_research(payload: ResearchCreate, actor: User = Depends(require_permissions("research.create")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, payload.cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    research = ResearchProject(id=new_id(), school_id=actor.school_id, cluster_id=payload.cluster_id, leader_id=actor.id, title=payload.title, status="DRAFT", mentor_id=db.scalar(select(User.id).where(User.school_id == actor.school_id, User.role == "MENTOR", User.active.is_(True))))
    db.add(research)
    db.flush()
    db.add(ResearchPlanVersion(id=new_id(), research_id=research.id, version=1, content={}, created_by=actor.id))
    audit(db, actor, "RESEARCH_CREATED", "RESEARCH_PROJECT", research.id, {"cluster_id": payload.cluster_id})
    db.commit()
    return research_dict(db, research)


@app.get(f"{API}/research-projects")
def list_research(actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    query = select(ResearchProject).where(ResearchProject.school_id == actor.school_id)
    if has_active_role(db, actor, "MENTOR") and not has_active_role(db, actor, "ADMIN", "STUDENT_PROJECT_LEADER"):
        query = query.where(ResearchProject.mentor_id == actor.id)
    elif has_active_role(db, actor, "STUDENT", "STUDENT_LEADER") and not has_active_role(db, actor, "ADMIN", "MENTOR"):
        query = query.where(ResearchProject.leader_id == actor.id)
    return [research_dict(db, r) for r in db.scalars(query.order_by(ResearchProject.updated_at.desc())).all()]


@app.get(f"{API}/research-projects/{{research_id}}")
def get_research(research_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    research = db.get(ResearchProject, research_id)
    if not research:
        raise HTTPException(404, "Research project not found.")
    require_same_school(actor, research.school_id)
    if has_active_role(db, actor, "STUDENT", "STUDENT_LEADER") and actor.id not in {research.leader_id}:
        raise HTTPException(403, "This research workspace is restricted.")
    if has_active_role(db, actor, "MENTOR") and not has_active_role(db, actor, "ADMIN") and research.mentor_id != actor.id:
        raise HTTPException(403, "This research workspace is not assigned to you.")
    return research_dict(db, research)


@app.put(f"{API}/research-projects/{{research_id}}/plan", dependencies=[Depends(require_csrf)])
def update_plan(research_id: str, payload: ResearchPlanUpdate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    research = db.get(ResearchProject, research_id)
    if not research:
        raise HTTPException(404, "Research project not found.")
    require_same_school(actor, research.school_id)
    if actor.id != research.leader_id and not has_active_role(db, actor, "ADMIN"):
        raise HTTPException(403, "Only the leader can edit this plan.")
    latest = db.scalars(select(ResearchPlanVersion).where(ResearchPlanVersion.research_id == research.id).order_by(ResearchPlanVersion.version.desc())).first()
    if latest and not latest.immutable:
        latest.content = payload.model_dump()
    else:
        db.add(ResearchPlanVersion(id=new_id(), research_id=research.id, version=(latest.version + 1 if latest else 1), content=payload.model_dump(), created_by=actor.id))
    if research.status == "CHANGES_REQUESTED":
        research.status = "DRAFT"
    audit(db, actor, "RESEARCH_PLAN_SAVED", "RESEARCH_PROJECT", research.id)
    db.commit()
    return research_dict(db, research)


@app.post(f"{API}/research-projects/{{research_id}}/submit-review", dependencies=[Depends(require_csrf)])
def submit_research_review(research_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    research = db.get(ResearchProject, research_id)
    if not research:
        raise HTTPException(404, "Research project not found.")
    require_same_school(actor, research.school_id)
    if actor.id != research.leader_id and not has_active_role(db, actor, "ADMIN"):
        raise HTTPException(403, "Only the leader can submit this plan.")
    latest = db.scalars(select(ResearchPlanVersion).where(ResearchPlanVersion.research_id == research.id).order_by(ResearchPlanVersion.version.desc())).first()
    missing = plan_missing(latest.content if latest else {})
    if missing:
        raise HTTPException(status_code=422, detail={"code": "RESEARCH_PLAN_INCOMPLETE", "message": "Complete required sections before mentor review.", "missing": missing})
    latest.immutable = True
    latest.submitted = True
    transition(db, actor, research, "RESEARCH_PROJECT", "MENTOR_REVIEW", RESEARCH_TRANSITIONS, "Leader requested mentor review")
    notify(db, research.mentor_id, "Research plan ready", f"{research.title} is ready for review.")
    db.commit()
    return research_dict(db, research)


@app.post(f"{API}/reviews", dependencies=[Depends(require_csrf)])
def create_review(payload: dict[str, Any], actor: User = Depends(require_roles("MENTOR", "OSIS", "MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    entity_type = str(payload.get("entity_type", ""))
    entity_id = str(payload.get("entity_id", ""))
    decision = str(payload.get("decision", "")).upper()
    reason = str(payload.get("reason", "")).strip()
    if len(reason) < 3:
        raise HTTPException(422, "A review reason is required.")
    entity = db.get(ResearchProject, entity_id) if entity_type == "RESEARCH_PROJECT" else db.get(ImpactProject, entity_id)
    if not entity:
        raise HTTPException(404, "Reviewable entity not found.")
    require_same_school(actor, entity.school_id)
    if entity_type == "RESEARCH_PROJECT":
        if has_active_role(db, actor, "MENTOR") and not has_active_role(db, actor, "ADMIN") and entity.mentor_id != actor.id:
            raise HTTPException(403, "This review is not assigned to you.")
        if decision not in {"APPROVED", "REQUEST_CHANGES"}:
            raise HTTPException(422, "Research decisions must be APPROVED or REQUEST_CHANGES.")
        target = "APPROVED" if decision == "APPROVED" else "CHANGES_REQUESTED"
        transition(db, actor, entity, "RESEARCH_PROJECT", target, RESEARCH_TRANSITIONS, reason)
        notify(db, entity.leader_id, "Research review decision", f"{entity.title}: {decision.replace('_', ' ').lower()}.")
    else:
        if decision not in {"APPROVED", "REQUEST_CHANGES", "PUBLISHED"}:
            raise HTTPException(422, "Impact decisions must be APPROVED, REQUEST_CHANGES, or PUBLISHED.")
        if decision == "APPROVED":
            target = "APPROVED"
        elif decision == "PUBLISHED":
            target = "PUBLISHED"
        else:
            target = "CHANGES_REQUESTED"
        transition(db, actor, entity, "IMPACT_PROJECT", target, IMPACT_TRANSITIONS, reason)
        notify(db, entity.leader_id, "Impact review decision", f"{entity.title}: {decision.replace('_', ' ').lower()}.")
    latest_version = db.scalars(select(ResearchPlanVersion).where(ResearchPlanVersion.research_id == entity_id).order_by(ResearchPlanVersion.version.desc())).first() if entity_type == "RESEARCH_PROJECT" else None
    db.add(Review(id=new_id(), school_id=actor.school_id, entity_type=entity_type, entity_id=entity_id, reviewer_id=actor.id, decision=decision, reason=reason, reviewed_version=latest_version.version if latest_version else None))
    audit(db, actor, "REVIEW_DECISION", entity_type, entity_id, {"decision": decision})
    db.commit()
    return {"entity_type": entity_type, "entity_id": entity_id, "decision": decision, "status": entity.status}


@app.post(f"{API}/surveys", dependencies=[Depends(require_csrf)])
def create_survey(payload: SurveyCreate, actor: User = Depends(require_roles("STUDENT_LEADER", "STUDENT", "MENTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    research = db.get(ResearchProject, payload.research_id)
    if not research:
        raise HTTPException(404, "Research project not found.")
    require_same_school(actor, research.school_id)
    survey = Survey(id=new_id(), school_id=actor.school_id, research_id=research.id, title=payload.title, purpose=payload.purpose, privacy_mode=payload.privacy_mode, one_response=payload.one_response, code=uuid4().hex[:12], created_by=actor.id)
    db.add(survey)
    audit(db, actor, "SURVEY_CREATED", "SURVEY", survey.id)
    db.commit()
    return {"id": survey.id, "title": survey.title, "status": survey.status, "code": survey.code, "questions": []}


@app.get(f"{API}/surveys/{{survey_id}}")
def get_survey(survey_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found.")
    require_same_school(actor, survey.school_id)
    questions = db.scalars(select(SurveyQuestion).where(SurveyQuestion.survey_id == survey.id).order_by(SurveyQuestion.position)).all()
    return {"id": survey.id, "title": survey.title, "purpose": survey.purpose, "privacy_mode": survey.privacy_mode, "status": survey.status, "code": survey.code, "questions": [{"id": q.id, "position": q.position, "question_type": q.question_type, "prompt": q.prompt, "options": q.options, "required": q.required} for q in questions]}


@app.post(f"{API}/surveys/{{survey_id}}/questions", dependencies=[Depends(require_csrf)])
def add_question(survey_id: str, payload: SurveyQuestionCreate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found.")
    require_same_school(actor, survey.school_id)
    if actor.id != survey.created_by and not has_active_role(db, actor, "MENTOR", "ADMIN"):
        raise HTTPException(403, "Only the survey team can edit this survey.")
    if survey.status != "DRAFT":
        raise HTTPException(409, "Approved or open survey versions are immutable.")
    count = db.scalar(select(func.count()).select_from(SurveyQuestion).where(SurveyQuestion.survey_id == survey.id)) or 0
    question = SurveyQuestion(id=new_id(), survey_id=survey.id, position=int(count) + 1, **payload.model_dump())
    db.add(question)
    db.commit()
    return {"id": question.id, "position": question.position}


@app.post(f"{API}/surveys/{{survey_id}}/publish", dependencies=[Depends(require_csrf)])
def publish_survey(survey_id: str, actor: User = Depends(require_roles("MENTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found.")
    require_same_school(actor, survey.school_id)
    questions = db.scalar(select(func.count()).select_from(SurveyQuestion).where(SurveyQuestion.survey_id == survey.id)) or 0
    if questions == 0:
        raise HTTPException(422, "A survey needs at least one question.")
    survey.status = "OPEN"
    audit(db, actor, "SURVEY_PUBLISHED", "SURVEY", survey.id)
    notify(db, survey.created_by, "Survey opened", f"{survey.title} is open for responses.")
    db.commit()
    return {"id": survey.id, "status": survey.status, "code": survey.code}


@app.get(f"{API}/public/surveys/{{code}}")
def public_survey(code: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    survey = db.scalar(select(Survey).where(Survey.code == code, Survey.status == "OPEN"))
    if not survey:
        raise HTTPException(404, "Survey is not available.")
    questions = db.scalars(select(SurveyQuestion).where(SurveyQuestion.survey_id == survey.id).order_by(SurveyQuestion.position)).all()
    return {"id": survey.id, "title": survey.title, "purpose": survey.purpose, "privacy_mode": survey.privacy_mode, "questions": [{"id": q.id, "type": q.question_type, "prompt": q.prompt, "options": q.options, "required": q.required} for q in questions]}


@app.post(f"{API}/public/surveys/{{code}}/responses")
def submit_survey_response(code: str, payload: SurveyResponseCreate, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    survey = db.scalar(select(Survey).where(Survey.code == code, Survey.status == "OPEN"))
    if not survey:
        raise HTTPException(404, "Survey is not available.")
    existing = db.scalar(select(SurveyResponse).where(SurveyResponse.idempotency_key == payload.idempotency_key))
    if existing:
        return {"status": "already_received", "response_id": existing.id}
    question_ids = {q.id for q in db.scalars(select(SurveyQuestion).where(SurveyQuestion.survey_id == survey.id)).all()}
    if not set(payload.answers).issubset(question_ids):
        raise HTTPException(422, "Response contains an unknown question.")
    # Anonymous surveys deliberately do not store the authenticated identity.
    respondent_id = None if survey.privacy_mode == "ANONYMOUS" else None
    db.add(SurveyResponse(id=new_id(), survey_id=survey.id, respondent_id=respondent_id, idempotency_key=payload.idempotency_key, answers=payload.answers))
    db.commit()
    return {"status": "received", "message": "Thank you. Your response was recorded."}


@app.get(f"{API}/surveys/{{survey_id}}/analysis")
def survey_analysis(survey_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found.")
    require_same_school(actor, survey.school_id)
    responses = db.scalars(select(SurveyResponse).where(SurveyResponse.survey_id == survey.id)).all()
    questions = db.scalars(select(SurveyQuestion).where(SurveyQuestion.survey_id == survey.id).order_by(SurveyQuestion.position)).all()
    results = []
    for question in questions:
        values = [r.answers.get(question.id) for r in responses if question.id in r.answers and r.answers.get(question.id) not in (None, "")]
        if question.question_type in {"MCQ", "LIKERT"}:
            counts: dict[str, int] = {}
            for value in values:
                counts[str(value)] = counts.get(str(value), 0) + 1
            results.append({"question_id": question.id, "prompt": question.prompt, "type": question.question_type, "valid_count": len(values), "counts": counts, "percentages": {k: round(v / len(values) * 100, 1) for k, v in counts.items()} if values else {}})
        elif question.question_type == "NUMBER":
            numbers = [float(v) for v in values if isinstance(v, (int, float)) or str(v).replace(".", "", 1).isdigit()]
            results.append({"question_id": question.id, "prompt": question.prompt, "type": question.question_type, "valid_count": len(numbers), "mean": round(mean(numbers), 2) if numbers else None, "median": median(numbers) if numbers else None})
        else:
            results.append({"question_id": question.id, "prompt": question.prompt, "type": question.question_type, "valid_count": len(values), "note": "Short text is not automatically summarized in V1."})
    return {"survey_id": survey.id, "response_count": len(responses), "privacy_mode": survey.privacy_mode, "results": results}


@app.get(f"{API}/surveys/{{survey_id}}/export")
def export_survey(survey_id: str, actor: User = Depends(require_roles("STUDENT_LEADER", "MENTOR", "ADMIN")), db: Session = Depends(get_db)) -> PlainTextResponse:
    survey = db.get(Survey, survey_id)
    if not survey:
        raise HTTPException(404, "Survey not found.")
    require_same_school(actor, survey.school_id)
    questions = db.scalars(select(SurveyQuestion).where(SurveyQuestion.survey_id == survey.id).order_by(SurveyQuestion.position)).all()
    responses = db.scalars(select(SurveyResponse).where(SurveyResponse.survey_id == survey.id)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["response_id"] + [q.prompt for q in questions])
    for response in responses:
        writer.writerow([response.id] + [response.answers.get(q.id, "") for q in questions])
    audit(db, actor, "SURVEY_EXPORTED", "SURVEY", survey.id, {"anonymous": survey.privacy_mode == "ANONYMOUS"})
    db.commit()
    return PlainTextResponse(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{survey.code}.csv"'})


@app.post(f"{API}/impact-projects", dependencies=[Depends(require_csrf)])
def create_impact(payload: ImpactCreate, actor: User = Depends(require_roles("STUDENT", "STUDENT_LEADER", "MENTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, payload.cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    project = ImpactProject(id=new_id(), school_id=actor.school_id, research_id=payload.research_id, cluster_id=payload.cluster_id, leader_id=actor.id, title=payload.title, mentor_id=db.scalar(select(User.id).where(User.school_id == actor.school_id, User.role == "MENTOR", User.active.is_(True))))
    db.add(project)
    audit(db, actor, "IMPACT_PROJECT_CREATED", "IMPACT_PROJECT", project.id, {"cluster_id": payload.cluster_id})
    db.commit()
    return impact_dict(db, project)


@app.get(f"{API}/impact-projects")
def list_impacts(actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    query = select(ImpactProject).where(ImpactProject.school_id == actor.school_id)
    if has_active_role(db, actor, "MENTOR") and not has_active_role(db, actor, "ADMIN"):
        query = query.where(ImpactProject.mentor_id == actor.id)
    elif has_active_role(db, actor, "STUDENT", "STUDENT_LEADER"):
        query = query.where(ImpactProject.leader_id == actor.id)
    return [impact_dict(db, p) for p in db.scalars(query.order_by(ImpactProject.updated_at.desc())).all()]


@app.get(f"{API}/impact-projects/{{project_id}}")
def get_impact(project_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if has_active_role(db, actor, "STUDENT", "STUDENT_LEADER") and not has_active_role(db, actor, "MENTOR", "ADMIN") and actor.id != project.leader_id:
        raise HTTPException(403, "This impact project is restricted.")
    if has_active_role(db, actor, "MENTOR") and not has_active_role(db, actor, "ADMIN") and project.mentor_id != actor.id:
        raise HTTPException(403, "This impact project is not assigned to you.")
    return impact_dict(db, project)


@app.patch(f"{API}/impact-projects/{{project_id}}", dependencies=[Depends(require_csrf)])
def update_impact(project_id: str, payload: ImpactUpdate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if actor.id != project.leader_id and not has_active_role(db, actor, "ADMIN") and not (has_active_role(db, actor, "MENTOR") and project.mentor_id == actor.id):
        raise HTTPException(403, "Only the project team can edit the proposal.")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(project, key, value)
    audit(db, actor, "IMPACT_PROPOSAL_SAVED", "IMPACT_PROJECT", project.id)
    db.commit()
    return impact_dict(db, project)


@app.post(f"{API}/impact-projects/{{project_id}}/submit-review", dependencies=[Depends(require_csrf)])
def submit_impact_review(project_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if actor.id != project.leader_id and not has_active_role(db, actor, "ADMIN"):
        raise HTTPException(403, "Only the project leader can submit this proposal.")
    missing = [name for name in ["target_users", "intervention", "theory_of_change", "risks", "resources"] if not getattr(project, name).strip()]
    primary = db.scalar(select(Metric).where(Metric.project_id == project.id, Metric.is_primary.is_(True), Metric.active.is_(True)))
    if missing or not primary:
        raise HTTPException(422, detail={"code": "IMPACT_PROPOSAL_INCOMPLETE", "missing": missing + ([] if primary else ["primary_metric"])})
    transition(db, actor, project, "IMPACT_PROJECT", "REVIEW", IMPACT_TRANSITIONS, "Leader requested intervention review")
    notify(db, project.mentor_id, "Impact proposal ready", f"{project.title} is ready for review.")
    db.commit()
    return impact_dict(db, project)


@app.post(f"{API}/impact-projects/{{project_id}}/metrics", dependencies=[Depends(require_csrf)])
def add_metric(project_id: str, payload: MetricCreate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if actor.id != project.leader_id and not has_active_role(db, actor, "ADMIN") and not (has_active_role(db, actor, "MENTOR") and project.mentor_id == actor.id):
        raise HTTPException(403, "Only the project team can add metrics.")
    active_metrics = db.scalars(select(Metric).where(Metric.project_id == project.id, Metric.active.is_(True))).all()
    if payload.is_primary and any(m.is_primary for m in active_metrics):
        raise HTTPException(409, "A project can have exactly one primary metric.")
    if not payload.is_primary and sum(1 for m in active_metrics if not m.is_primary) >= 3:
        raise HTTPException(409, "A project can have no more than three secondary metrics in V1.")
    metric = Metric(id=new_id(), project_id=project.id, **payload.model_dump())
    db.add(metric)
    audit(db, actor, "METRIC_CREATED", "IMPACT_METRIC", metric.id, {"project_id": project.id, "primary": metric.is_primary})
    db.commit()
    return impact_dict(db, project)


@app.post(f"{API}/impact-metrics/{{metric_id}}/observations", dependencies=[Depends(require_csrf)])
def add_observation(metric_id: str, payload: ObservationCreate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    metric = db.get(Metric, metric_id)
    if not metric:
        raise HTTPException(404, "Metric not found.")
    project = db.get(ImpactProject, metric.project_id)
    require_same_school(actor, project.school_id)
    if actor.id != project.leader_id and not has_active_role(db, actor, "ADMIN") and not (has_active_role(db, actor, "MENTOR") and project.mentor_id == actor.id):
        raise HTTPException(403, "Only the project team can record observations.")
    if payload.phase in {"POST", "DURING", "FOLLOW_UP"} and project.status not in {"ACTIVE", "PAUSED", "COMPLETED", "IMPACT_REVIEW", "PUBLISHED"}:
        raise HTTPException(409, "Record a baseline before during/post observations.")
    observation = Observation(id=new_id(), metric_id=metric.id, project_id=project.id, recorder_id=actor.id, **payload.model_dump())
    db.add(observation)
    audit(db, actor, "OBSERVATION_RECORDED", "IMPACT_METRIC", metric.id, {"phase": payload.phase})
    db.commit()
    return impact_dict(db, project)


@app.post(f"{API}/impact-projects/{{project_id}}/activate", dependencies=[Depends(require_csrf)])
def activate_impact(project_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if actor.id != project.leader_id and not has_active_role(db, actor, "ADMIN") and not (has_active_role(db, actor, "MENTOR") and project.mentor_id == actor.id):
        raise HTTPException(403, "Only an authorized project member can activate the project.")
    primary = db.scalar(select(Metric).where(Metric.project_id == project.id, Metric.is_primary.is_(True), Metric.active.is_(True)))
    baseline = db.scalar(select(Observation).where(Observation.project_id == project.id, Observation.metric_id == (primary.id if primary else "none"), Observation.phase == "BASELINE")) if primary else None
    if not primary or not baseline:
        raise HTTPException(status_code=409, detail={"code": "BASELINE_REQUIRED", "message": "A primary metric and baseline observation are required before activation."})
    transition(db, actor, project, "IMPACT_PROJECT", "ACTIVE", IMPACT_TRANSITIONS, "Baseline gate passed")
    audit(db, actor, "PROJECT_ACTIVATED", "IMPACT_PROJECT", project.id)
    db.commit()
    return impact_dict(db, project)


@app.get(f"{API}/impact-projects/{{project_id}}/report")
def get_impact_report(project_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if has_active_role(db, actor, "STUDENT", "STUDENT_LEADER") and not has_active_role(db, actor, "MENTOR", "ADMIN") and actor.id != project.leader_id:
        raise HTTPException(403, "This report is restricted.")
    current = db.scalars(select(ImpactReport).where(ImpactReport.project_id == project.id).order_by(ImpactReport.version.desc())).first()
    if not current:
        data = impact_dict(db, project)
        current = ImpactReport(id=new_id(), project_id=project.id, version=1, content={"problem": "", "evidence": "", "research_question": "", "intervention": project.intervention, "theory_of_change": project.theory_of_change, "implementation": "", "results": data["metrics"], "what_changed": "Observed change only; no automatic causal claim.", "limitations": "", "what_did_not_work": "", "negative_or_inconclusive_findings": "", "next_steps": "", "evidence_appendix": []}, created_by=actor.id)
        db.add(current)
        db.commit()
    return {"project_id": project.id, "version": current.version, "immutable": current.immutable, "status": project.status, "content": current.content}


@app.put(f"{API}/impact-projects/{{project_id}}/report", dependencies=[Depends(require_csrf)])
def update_impact_report(project_id: str, payload: ReportUpdate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if actor.id != project.leader_id and not has_active_role(db, actor, "ADMIN") and not (has_active_role(db, actor, "MENTOR") and project.mentor_id == actor.id):
        raise HTTPException(403, "Only the project team can edit the report.")
    current = db.scalars(select(ImpactReport).where(ImpactReport.project_id == project.id).order_by(ImpactReport.version.desc())).first()
    if current and not current.immutable:
        current.content = payload.content
    else:
        db.add(ImpactReport(id=new_id(), project_id=project.id, version=(current.version + 1 if current else 1), content=payload.content, created_by=actor.id))
    audit(db, actor, "IMPACT_REPORT_SAVED", "IMPACT_PROJECT", project.id)
    db.commit()
    return get_impact_report(project_id, actor, db)


@app.post(f"{API}/impact-projects/{{project_id}}/submit-report", dependencies=[Depends(require_csrf)])
def submit_impact_report(project_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    current = db.scalars(select(ImpactReport).where(ImpactReport.project_id == project.id).order_by(ImpactReport.version.desc())).first()
    if not current or not current.content.get("limitations"):
        raise HTTPException(422, "The impact report needs a limitations section before review.")
    current.immutable = True
    if project.status == "ACTIVE":
        transition(db, actor, project, "IMPACT_PROJECT", "COMPLETED", IMPACT_TRANSITIONS, "Team submitted implementation")
    transition(db, actor, project, "IMPACT_PROJECT", "IMPACT_REVIEW", IMPACT_TRANSITIONS, "Impact report submitted")
    notify(db, project.mentor_id, "Impact report ready", f"{project.title} is ready for impact review.")
    db.commit()
    return impact_dict(db, project)


@app.get(f"{API}/tasks/mine")
@app.get(f"{API}/tasks")
def list_my_tasks(status_filter: str = "", project_id: str = "", actor: User = Depends(require_permissions("task.read_assigned")), db: Session = Depends(get_db)) -> dict[str, Any]:
    query = select(ProjectTask).join(ImpactProject, ImpactProject.id == ProjectTask.project_id).where(ImpactProject.school_id == actor.school_id, ProjectTask.owner_id == actor.id)
    if status_filter.strip():
        query = query.where(ProjectTask.status == status_filter.upper())
    if project_id.strip():
        query = query.where(ProjectTask.project_id == project_id)
    tasks = db.scalars(query.order_by(ProjectTask.due_date, ProjectTask.title)).all()
    return {"items": [{"id": task.id, "title": task.title, "status": task.status, "priority": task.priority, "due_date": task.due_date, "owner_id": task.owner_id, "project_id": task.project_id, "href": f"/app/projects/{task.project_id}"} for task in tasks]}


@app.patch(f"{API}/tasks/{{task_id}}", dependencies=[Depends(require_csrf)])
def update_task(task_id: str, payload: TaskUpdate, actor: User = Depends(require_permissions("task.update_assigned")), db: Session = Depends(get_db)) -> dict[str, Any]:
    task = db.get(ProjectTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found.")
    project = db.get(ImpactProject, task.project_id)
    if not project or project.school_id != actor.school_id or task.owner_id != actor.id:
        raise HTTPException(404, "Task not found.")
    previous = task.status
    task.status = payload.status
    audit(db, actor, "TASK_STATUS_UPDATED", "PROJECT_TASK", task.id, {"from": previous, "to": task.status})
    db.commit()
    return {"id": task.id, "title": task.title, "status": task.status, "priority": task.priority, "due_date": task.due_date, "owner_id": task.owner_id, "project_id": task.project_id, "href": f"/app/projects/{task.project_id}"}


@app.get(f"{API}/mentor/attention")
@app.get(f"{API}/mentor/reviews")
def mentor_attention(actor: User = Depends(require_roles("MENTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    research = db.scalars(select(ResearchProject).where(ResearchProject.school_id == actor.school_id, ResearchProject.mentor_id == actor.id, ResearchProject.status == "MENTOR_REVIEW")).all()
    projects = db.scalars(select(ImpactProject).where(ImpactProject.school_id == actor.school_id, ImpactProject.mentor_id == actor.id)).all()
    items: list[dict[str, Any]] = [{"id": r.id, "entity_type": "RESEARCH_PROJECT", "title": r.title, "reason": "Research plan needs review", "status": r.status, "owner_id": r.leader_id} for r in research]
    for project in projects:
        primary = db.scalar(select(Metric).where(Metric.project_id == project.id, Metric.is_primary.is_(True), Metric.active.is_(True)))
        baseline = db.scalar(select(Observation).where(Observation.project_id == project.id, Observation.phase == "BASELINE"))
        if project.status in {"REVIEW", "IMPACT_REVIEW"}:
            items.append({"id": project.id, "entity_type": "IMPACT_PROJECT", "title": project.title, "reason": "Impact work needs review", "status": project.status, "owner_id": project.leader_id})
        elif project.status == "APPROVED" and (not primary or not baseline):
            items.append({"id": project.id, "entity_type": "IMPACT_PROJECT", "title": project.title, "reason": "Missing primary metric or baseline", "status": project.status, "owner_id": project.leader_id})
    return {"items": items}


@app.get(f"{API}/osis/overview")
def osis_overview(actor: User = Depends(require_roles("OSIS", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.school_id == actor.school_id, ProblemCluster.status.in_(["VALIDATED", "ACTION_PLANNED", "ACTION_UNDERWAY", "RESOLVED", "IMPACT_MEASURED"]))).all()
    return {"validated_clusters": [cluster_dict(db, c, actor) for c in clusters], "non_sensitive_only": True, "publication_rule": "Official updates are append-only."}


@app.get(f"{API}/notifications")
def notifications(actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(Notification).where(Notification.user_id == actor.id).order_by(Notification.created_at.desc()).limit(50)).all()
    return [{"id": n.id, "title": n.title, "message": n.message, "read": n.read, "created_at": dt(n.created_at)} for n in rows]


@app.post(f"{API}/notifications/{{notification_id}}/read", dependencies=[Depends(require_csrf)])
def mark_notification_read(notification_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    notification = db.get(Notification, notification_id)
    if not notification or notification.user_id != actor.id:
        raise HTTPException(404, "Notification not found.")
    notification.read = True
    db.commit()
    return {"status": "read"}


def feedback_dict(item: Feedback) -> dict[str, Any]:
    return {"id": item.id, "category": item.category, "description": item.description, "severity": item.severity, "allow_contact": item.allow_contact, "route": item.route, "user_role": item.user_role, "browser": item.browser, "screen_size": item.screen_size, "app_version": item.app_version, "status": item.status, "created_at": dt(item.created_at), "updated_at": dt(item.updated_at)}


@app.post(f"{API}/feedback", dependencies=[Depends(require_csrf)])
def create_feedback(payload: FeedbackCreate, request: Request, actor: User = Depends(require_permissions("feedback.submit")), db: Session = Depends(get_db)) -> dict[str, Any]:
    enforce_rate_limit(request, "feedback", limit=5, window_seconds=600)
    item = Feedback(id=new_id(), school_id=actor.school_id, reporter_id=actor.id, **payload.model_dump())
    db.add(item)
    audit(db, actor, "FEEDBACK_SUBMITTED", "FEEDBACK", item.id, {"category": item.category, "severity": item.severity, "route": item.route}, request=request)
    db.commit()
    return {"message": "Thank you. Your feedback was sent to the ImpactOS team.", "feedback": feedback_dict(item)}


@app.get(f"{API}/admin/feedback")
def admin_feedback(actor: User = Depends(require_permissions("admin.feedback.read")), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(Feedback).where(Feedback.school_id == actor.school_id).order_by(Feedback.created_at.desc()).limit(100)).all()
    return [feedback_dict(item) for item in rows]


@app.patch(f"{API}/admin/feedback/{{feedback_id}}", dependencies=[Depends(require_csrf)])
def update_feedback(feedback_id: str, payload: dict[str, Any], request: Request, actor: User = Depends(require_permissions("admin.feedback.read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    item = db.get(Feedback, feedback_id)
    if not item or item.school_id != actor.school_id:
        raise HTTPException(404, "Feedback not found.")
    next_status = str(payload.get("status", "")).upper()
    if next_status not in {"NEW", "TRIAGED", "PLANNED", "RESOLVED", "CLOSED"}:
        raise HTTPException(422, "Feedback status is invalid.")
    item.status = next_status
    audit(db, actor, "FEEDBACK_STATUS_UPDATED", "FEEDBACK", item.id, {"status": next_status}, request=request)
    db.commit()
    return feedback_dict(item)


@app.get(f"{API}/admin/audit-logs")
def audit_logs(actor: User = Depends(require_roles("ADMIN", "MODERATOR")), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(AuditLog).where(AuditLog.school_id == actor.school_id).order_by(AuditLog.created_at.desc()).limit(100)).all()
    return [{"id": row.id, "actor_id": row.actor_id, "action": row.action, "entity_type": row.entity_type, "entity_id": row.entity_id, "metadata": row.metadata_safe, "created_at": dt(row.created_at)} for row in rows]


@app.get(f"{API}/admin/audit")
def phase_one_audit_logs(actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return audit_logs(actor=actor, db=db)


def member_summary(db: Session, user: User) -> dict[str, Any]:
    return {**user_dict(user), "roles": active_role_codes(db, user), "permissions": active_permissions(db, user), "membership_id": db.scalar(select(Membership.id).where(Membership.user_id == user.id, Membership.school_id == user.school_id))}


@app.get(f"{API}/admin/members")
def admin_members(search: str | None = None, status_filter: str | None = None, role_filter: str | None = None, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    query = select(User).where(User.school_id == actor.school_id).order_by(User.created_at)
    if search:
        term = f"%{search.strip().lower()}%"
        query = query.where(func.lower(User.email).like(term) | func.lower(User.display_name).like(term))
    users = db.scalars(query).all()
    rows = [member_summary(db, user) for user in users]
    if status_filter:
        rows = [row for row in rows if row.get("status") == status_filter.upper()]
    if role_filter:
        rows = [row for row in rows if normalize_role(role_filter.upper()) in row.get("roles", [])]
    return rows


def find_membership(db: Session, membership_id: str, school_id: str) -> Membership:
    membership = db.scalar(select(Membership).where(Membership.id == membership_id, Membership.school_id == school_id))
    if membership:
        return membership
    membership = db.scalar(select(Membership).join(User, User.id == Membership.user_id).where(User.id == membership_id, Membership.school_id == school_id))
    if membership:
        return membership
    raise HTTPException(404, detail={"code": "MEMBER_NOT_FOUND", "message": "Member not found."})


@app.patch(f"{API}/admin/members/{{membership_id}}/roles", dependencies=[Depends(require_csrf)])
def update_member_roles(membership_id: str, payload: RoleAssignmentRequest, request: Request, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    membership = find_membership(db, membership_id, actor.school_id)
    desired = {normalize_role(role.upper()) for role in payload.roles}
    if not desired or not desired.issubset(set(ROLE_DETAILS)):
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "One or more roles are invalid."})
    current = set(active_role_codes(db, db.get(User, membership.user_id)))
    if "ADMINISTRATOR" in current and "ADMINISTRATOR" not in desired:
        remaining = db.scalar(select(func.count()).select_from(User).join(Membership, Membership.user_id == User.id).join(RoleAssignment, RoleAssignment.membership_id == Membership.id).join(Role, Role.id == RoleAssignment.role_id).where(User.school_id == actor.school_id, User.active.is_(True), Role.code == "ADMINISTRATOR", RoleAssignment.revoked_at.is_(None), User.id != membership.user_id)) or 0
        if remaining < 1:
            raise HTTPException(409, detail={"code": "FINAL_ADMIN_PROTECTED", "message": "The final active administrator cannot lose administrator access."})
    target = db.get(User, membership.user_id)
    ensure_identity_records(db, target, list(desired), actor.id)
    assignments = db.scalars(select(RoleAssignment).where(RoleAssignment.membership_id == membership.id)).all()
    for assignment in assignments:
        role = db.get(Role, assignment.role_id)
        if role and role.code not in desired and assignment.revoked_at is None:
            assignment.revoked_at = datetime.utcnow()
    target.role = {"STUDENT_CONTRIBUTOR": "STUDENT", "STUDENT_PROJECT_LEADER": "STUDENT_LEADER", "OSIS_REVIEWER": "OSIS", "ADMINISTRATOR": "ADMIN"}.get(sorted(desired)[0], sorted(desired)[0])
    audit(db, actor, "MEMBER_ROLES_UPDATED", "MEMBERSHIP", membership.id, {"roles": sorted(desired)}, request=request)
    db.commit()
    return member_summary(db, target)


@app.post(f"{API}/admin/members/{{membership_id}}/deactivate", dependencies=[Depends(require_csrf)])
def deactivate_member(membership_id: str, request: Request, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    membership = find_membership(db, membership_id, actor.school_id)
    target = db.get(User, membership.user_id)
    if target.id == actor.id:
        raise HTTPException(409, detail={"code": "SELF_DEACTIVATION_BLOCKED", "message": "You cannot deactivate your own administrator account."})
    if "ADMINISTRATOR" in active_role_codes(db, target):
        remaining = db.scalar(select(func.count()).select_from(User).join(Membership, Membership.user_id == User.id).join(RoleAssignment, RoleAssignment.membership_id == Membership.id).join(Role, Role.id == RoleAssignment.role_id).where(User.school_id == actor.school_id, User.active.is_(True), User.id != target.id, Role.code == "ADMINISTRATOR", RoleAssignment.revoked_at.is_(None))) or 0
        if remaining < 1:
            raise HTTPException(409, detail={"code": "FINAL_ADMIN_PROTECTED", "message": "The final active administrator cannot be deactivated."})
    target.active = False
    target.status = "DEACTIVATED"
    membership.status = "DEACTIVATED"
    sessions = revoke_all_sessions(db, target.id)
    audit(db, actor, "ACCOUNT_DEACTIVATED", "USER", target.id, {"sessions_revoked": sessions}, request=request)
    db.commit()
    return member_summary(db, target)


@app.post(f"{API}/admin/members/{{membership_id}}/reactivate", dependencies=[Depends(require_csrf)])
def reactivate_member(membership_id: str, request: Request, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    membership = find_membership(db, membership_id, actor.school_id)
    target = db.get(User, membership.user_id)
    target.active = True
    target.status = "ACTIVE"
    membership.status = "ACTIVE"
    audit(db, actor, "ACCOUNT_REACTIVATED", "USER", target.id, request=request)
    db.commit()
    return member_summary(db, target)


@app.get(f"{API}/admin/settings")
def get_settings(actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    settings = db.get(SchoolSetting, actor.school_id)
    return settings.settings if settings else {}


@app.put(f"{API}/admin/settings", dependencies=[Depends(require_csrf)])
def update_settings(payload: dict[str, Any], actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    settings = db.get(SchoolSetting, actor.school_id)
    if not settings:
        settings = SchoolSetting(school_id=actor.school_id, settings={})
        db.add(settings)
    allowed = {"school_name", "urgent_help_notice", "private_report_owner_role", "allowed_categories", "retention_reference", "publication_policy", "ui_language", "stale_project_days"}
    settings.settings = {key: value for key, value in payload.items() if key in allowed}
    audit(db, actor, "SCHOOL_SETTINGS_UPDATED", "SCHOOL", actor.school_id, {"keys": list(settings.settings)})
    db.commit()
    return settings.settings


@app.post(f"{API}/admin/invitations", dependencies=[Depends(require_csrf)])
def create_invitation(payload: InvitationCreate, request: Request, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "Enter a valid email address."})
    existing = db.scalar(select(User).where(User.email == email, User.active.is_(True)))
    if existing:
        raise HTTPException(409, detail={"code": "ACCOUNT_EXISTS", "message": "An active account already exists for this email."})
    role_codes = [normalize_role(role.upper()) for role in (payload.roles or [payload.role])]
    if not role_codes or not set(role_codes).issubset(set(ROLE_DETAILS)):
        raise HTTPException(422, detail={"code": "VALIDATION_ERROR", "message": "One or more roles are invalid."})
    raw = secrets.token_urlsafe(32)
    invitation = Invitation(id=new_id(), school_id=actor.school_id, email=email, role={"STUDENT_CONTRIBUTOR": "STUDENT", "STUDENT_PROJECT_LEADER": "STUDENT_LEADER", "OSIS_REVIEWER": "OSIS", "ADMINISTRATOR": "ADMIN"}.get(role_codes[0], role_codes[0]), token_hash=secure_token_hash(raw), expires_at=datetime.utcnow() + timedelta(days=payload.expires_in_days), status="PENDING", created_by=actor.id, invited_by=actor.id)
    db.add(invitation)
    db.flush()
    for code in role_codes:
        role = db.scalar(select(Role).where(Role.code == code))
        if not role:
            name, description = ROLE_DETAILS[code]
            role = Role(id=new_id(), code=code, name=name, description=description)
            db.add(role)
            db.flush()
        db.add(InvitationRole(invitation_id=invitation.id, role_id=role.id))
    audit(db, actor, "INVITATION_CREATED", "INVITATION", invitation.id, {"roles": role_codes}, request=request)
    db.commit()
    return {"id": invitation.id, "email": invitation.email, "role": invitation.role, "roles": role_codes, "expires_at": dt(invitation.expires_at), "token": raw, "activation_path": f"/activate?token={raw}"}


@app.get(f"{API}/admin/invitations")
def list_invitations(actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(Invitation).where(Invitation.school_id == actor.school_id).order_by(Invitation.created_at.desc())).all()
    return [{"id": row.id, "email": row.email, "role": row.role, "roles": [result[0] for result in db.execute(select(Role.code).join(InvitationRole, InvitationRole.role_id == Role.id).where(InvitationRole.invitation_id == row.id)).all()] or [normalize_role(row.role)], "state": invitation_state(row), "expires_at": dt(row.expires_at), "created_at": dt(row.created_at)} for row in rows]


@app.post(f"{API}/admin/invitations/{{invitation_id}}/revoke", dependencies=[Depends(require_csrf)])
def revoke_invitation(invitation_id: str, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, str]:
    invitation = db.get(Invitation, invitation_id)
    if not invitation or invitation.school_id != actor.school_id:
        raise HTTPException(404, detail={"code": "INVITATION_INVALID", "message": "Invitation not found."})
    if invitation_state(invitation) == "USED":
        raise HTTPException(409, "Used invitations cannot be revoked.")
    invitation.revoked_at = datetime.utcnow()
    invitation.status = "REVOKED"
    audit(db, actor, "INVITATION_REVOKED", "INVITATION", invitation.id)
    db.commit()
    return {"status": "revoked"}


@app.post(f"{API}/admin/invitations/{{invitation_id}}/resend", dependencies=[Depends(require_csrf)])
def resend_invitation(invitation_id: str, request: Request, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    old = db.get(Invitation, invitation_id)
    if not old or old.school_id != actor.school_id:
        raise HTTPException(404, detail={"code": "INVITATION_INVALID", "message": "Invitation not found."})
    if invitation_state(old) == "USED":
        raise HTTPException(409, detail={"code": "INVITATION_USED", "message": "Used invitations cannot be resent."})
    old.status = "REVOKED"
    old.revoked_at = datetime.utcnow()
    raw = secrets.token_urlsafe(32)
    replacement = Invitation(id=new_id(), school_id=old.school_id, email=old.email, role=old.role, token_hash=secure_token_hash(raw), expires_at=datetime.utcnow() + timedelta(days=7), status="PENDING", created_by=actor.id, invited_by=actor.id)
    db.add(replacement)
    db.flush()
    for role_code in [normalize_role(old.role)]:
        role = db.scalar(select(Role).where(Role.code == role_code))
        if role:
            db.add(InvitationRole(invitation_id=replacement.id, role_id=role.id))
    audit(db, actor, "INVITATION_CREATED", "INVITATION", replacement.id, {"resend_of": old.id}, request=request)
    db.commit()
    return {"id": replacement.id, "email": replacement.email, "token": raw, "activation_path": f"/activate?token={raw}", "expires_at": dt(replacement.expires_at)}


@app.post(f"{API}/admin/public-impact-stories", dependencies=[Depends(require_csrf)])
def create_public_story(payload: dict[str, Any], actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    required = ["slug", "title", "problem_summary", "intervention_summary", "measurement_summary", "observed_result", "limitations"]
    missing = [key for key in required if not str(payload.get(key, "")).strip()]
    if missing:
        raise HTTPException(422, detail={"code": "PUBLIC_STORY_INCOMPLETE", "missing": missing})
    slug = re.sub(r"[^a-z0-9-]+", "-", str(payload["slug"]).lower()).strip("-")
    if not slug or db.scalar(select(PublicImpactStory).where(PublicImpactStory.slug == slug)):
        raise HTTPException(409, "That public story slug is unavailable.")
    story = PublicImpactStory(id=new_id(), school_id=actor.school_id, slug=slug, title=str(payload["title"]).strip(), problem_summary=str(payload["problem_summary"]).strip(), evidence_summary=payload.get("evidence_summary"), research_question=payload.get("research_question"), intervention_summary=str(payload["intervention_summary"]).strip(), measurement_summary=str(payload["measurement_summary"]).strip(), observed_result=str(payload["observed_result"]).strip(), limitations=str(payload["limitations"]).strip(), what_did_not_work=payload.get("what_did_not_work"), next_steps=payload.get("next_steps"), official_response=payload.get("official_response"), category=payload.get("category"), result_type=str(payload.get("result_type", "INCONCLUSIVE")).upper(), public_team_label=payload.get("public_team_label"), is_synthetic=bool(payload.get("is_synthetic", app_mode() == "DEMO")), status="DRAFT")
    db.add(story)
    audit(db, actor, "PUBLIC_STORY_CREATED", "PUBLIC_IMPACT_STORY", story.id, {"slug": story.slug})
    db.commit()
    return {"id": story.id, **public_story_dict(story)}


@app.patch(f"{API}/admin/public-impact-stories/{{story_id}}", dependencies=[Depends(require_csrf)])
def update_public_story(story_id: str, payload: dict[str, Any], actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    story = db.get(PublicImpactStory, story_id)
    if not story or story.school_id != actor.school_id:
        raise HTTPException(404, "Public story not found.")
    if story.status in {"PUBLISHED", "WITHDRAWN"}:
        raise HTTPException(409, "Published or withdrawn stories require a new version.")
    allowed = {"title", "problem_summary", "evidence_summary", "research_question", "intervention_summary", "measurement_summary", "observed_result", "limitations", "what_did_not_work", "next_steps", "official_response", "category", "result_type", "public_team_label", "is_synthetic"}
    for key, value in payload.items():
        if key in allowed:
            setattr(story, key, value)
    story.version += 1
    audit(db, actor, "PUBLIC_STORY_UPDATED", "PUBLIC_IMPACT_STORY", story.id, {"version": story.version})
    db.commit()
    return {"id": story.id, **public_story_dict(story)}


@app.post(f"{API}/admin/public-impact-stories/{{story_id}}/submit-review", dependencies=[Depends(require_csrf)])
def submit_public_story_review(story_id: str, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, str]:
    story = db.get(PublicImpactStory, story_id)
    if not story or story.school_id != actor.school_id:
        raise HTTPException(404, "Public story not found.")
    if story.status != "DRAFT":
        raise HTTPException(409, "Only draft stories can be submitted.")
    story.status = "REVIEW"
    audit(db, actor, "PUBLIC_STORY_SUBMITTED", "PUBLIC_IMPACT_STORY", story.id)
    db.commit()
    return {"status": story.status}


@app.post(f"{API}/admin/public-impact-stories/{{story_id}}/approve", dependencies=[Depends(require_csrf)])
def approve_public_story(story_id: str, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, str]:
    story = db.get(PublicImpactStory, story_id)
    if not story or story.school_id != actor.school_id:
        raise HTTPException(404, "Public story not found.")
    if story.status != "REVIEW":
        raise HTTPException(409, "Only stories in review can be approved.")
    story.status = "APPROVED"
    story.approved_by = actor.id
    story.approved_at = datetime.utcnow()
    audit(db, actor, "PUBLIC_STORY_APPROVED", "PUBLIC_IMPACT_STORY", story.id)
    db.commit()
    return {"status": story.status}


@app.post(f"{API}/admin/public-impact-stories/{{story_id}}/publish", dependencies=[Depends(require_csrf)])
def publish_public_story(story_id: str, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, str]:
    story = db.get(PublicImpactStory, story_id)
    if not story or story.school_id != actor.school_id:
        raise HTTPException(404, "Public story not found.")
    if story.status != "APPROVED":
        raise HTTPException(409, "Only approved stories can be published.")
    story.status = "PUBLISHED"
    story.published_by = actor.id
    story.published_at = datetime.utcnow()
    audit(db, actor, "PUBLIC_STORY_PUBLISHED", "PUBLIC_IMPACT_STORY", story.id, {"slug": story.slug})
    db.commit()
    return {"status": story.status, "slug": story.slug}


@app.post(f"{API}/admin/public-impact-stories/{{story_id}}/withdraw", dependencies=[Depends(require_csrf)])
def withdraw_public_story(story_id: str, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> dict[str, str]:
    story = db.get(PublicImpactStory, story_id)
    if not story or story.school_id != actor.school_id:
        raise HTTPException(404, "Public story not found.")
    story.status = "WITHDRAWN"
    story.withdrawn_at = datetime.utcnow()
    audit(db, actor, "PUBLIC_STORY_WITHDRAWN", "PUBLIC_IMPACT_STORY", story.id)
    db.commit()
    return {"status": story.status}
