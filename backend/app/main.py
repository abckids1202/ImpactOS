from __future__ import annotations

import csv
import io
import os
import re
from datetime import datetime
from statistics import mean, median
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import SessionLocal, get_db, init_db
from .models import (
    AuditLog,
    Evidence,
    ImpactProject,
    ImpactReport,
    Metric,
    Notification,
    Observation,
    OfficialUpdate,
    ProblemCluster,
    ProblemReport,
    ProblemSignal,
    ProjectTask,
    ResearchPlanVersion,
    ResearchProject,
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
    ImpactCreate,
    ImpactUpdate,
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
    SurveyCreate,
    SurveyQuestionCreate,
    SurveyResponseCreate,
    UserRead,
)
from .security import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    create_session,
    get_current_user,
    hash_password,
    require_csrf,
    require_roles,
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

API = "/api/v1"
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo1234")


def new_id() -> str:
    return str(uuid4())


def dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def user_dict(user: User) -> dict[str, Any]:
    return UserRead.model_validate(user).model_dump()


def audit(db: Session, actor: User | None, action: str, entity_type: str, entity_id: str | None, metadata: dict[str, Any] | None = None) -> None:
    if not actor:
        return
    db.add(
        AuditLog(
            id=new_id(),
            school_id=actor.school_id,
            actor_id=actor.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_safe=metadata or {},
        )
    )


def notify(db: Session, user_id: str | None, title: str, message: str) -> None:
    if user_id:
        db.add(Notification(id=new_id(), user_id=user_id, title=title, message=message))


def require_same_school(actor: User, school_id: str) -> None:
    if actor.school_id != school_id:
        raise HTTPException(status_code=404, detail="Record not found.")


def role_guard(actor: User, *roles: str) -> None:
    if actor.role not in roles:
        raise HTTPException(status_code=403, detail="You do not have permission for this action.")


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
    "DRAFT": {"MODERATION_REVIEW", "PRIVATE_REVIEW"},
    "MODERATION_REVIEW": {"PUBLISHED", "PRIVATE_REVIEW", "ARCHIVED"},
    "PRIVATE_REVIEW": {"PUBLISHED", "ARCHIVED"},
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
    show_author = report.visibility != "SCHOOL_ANONYMOUS" or actor.role in {"MODERATOR", "ADMIN"} or actor.id == report.author_id
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
        "sensitivity_reason": report.sensitivity_reason if actor.role in {"MODERATOR", "ADMIN"} else None,
        "created_at": dt(report.created_at),
        "updated_at": dt(report.updated_at),
    }


def cluster_dict(db: Session, cluster: ProblemCluster, actor: User) -> dict[str, Any]:
    reports = db.scalars(select(ProblemReport).where(ProblemReport.cluster_id == cluster.id)).all()
    signals = db.scalars(select(ProblemSignal).where(ProblemSignal.cluster_id == cluster.id)).all()
    evidence = db.scalars(select(Evidence).where(Evidence.cluster_id == cluster.id)).all()
    updates = db.scalars(select(OfficialUpdate).where(OfficialUpdate.cluster_id == cluster.id).order_by(OfficialUpdate.created_at.desc())).all()
    signal_counts: dict[str, int] = {}
    for signal in signals:
        signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
    visible_reports = [r for r in reports if r.status in {"PUBLISHED", "MERGED"} or actor.role in {"MODERATOR", "ADMIN"}]
    return {
        "id": cluster.id,
        "title": cluster.title,
        "summary": cluster.summary,
        "category": cluster.category,
        "scope": cluster.scope,
        "status": cluster.status,
        "priority_rationale": cluster.priority_rationale,
        "affected_count": signal_counts.get("AFFECTS_ME", 0),
        "evidence_count": len(evidence),
        "report_count": len(visible_reports),
        "signal_counts": signal_counts,
        "reports": [report_dict(db, r, actor) for r in visible_reports],
        "evidence": [{"id": e.id, "source": e.source, "type": e.evidence_type, "observation_date": e.observation_date, "relevance": e.relevance, "visibility": e.visibility, "file_name": e.file_name} for e in evidence],
        "official_updates": [{"id": u.id, "status": u.status, "message": u.message, "created_at": dt(u.created_at)} for u in updates],
        "created_at": dt(cluster.created_at),
        "updated_at": dt(cluster.updated_at),
    }


def research_dict(db: Session, research: ResearchProject) -> dict[str, Any]:
    versions = db.scalars(select(ResearchPlanVersion).where(ResearchPlanVersion.research_id == research.id).order_by(ResearchPlanVersion.version.desc())).all()
    plan = versions[0].content if versions else {}
    return {"id": research.id, "title": research.title, "cluster_id": research.cluster_id, "leader_id": research.leader_id, "mentor_id": research.mentor_id, "status": research.status, "plan": plan, "plan_version": versions[0].version if versions else 0, "plan_immutable": versions[0].immutable if versions else False, "missing_sections": plan_missing(plan), "created_at": dt(research.created_at), "updated_at": dt(research.updated_at)}


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
    return {"id": project.id, "title": project.title, "research_id": project.research_id, "cluster_id": project.cluster_id, "leader_id": project.leader_id, "mentor_id": project.mentor_id, "status": project.status, "target_users": project.target_users, "intervention": project.intervention, "theory_of_change": project.theory_of_change, "risks": project.risks, "resources": project.resources, "metrics": metric_rows, "tasks": [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "due_date": t.due_date} for t in tasks], "report": report.content if report else None, "report_version": report.version if report else 0, "created_at": dt(project.created_at), "updated_at": dt(project.updated_at)}


def seed_demo() -> None:
    db = SessionLocal()
    try:
        school = db.get(School, "school-pilar")
        if not school:
            school = School(id="school-pilar", name="Sekolah Pilar Indonesia", slug="pilar-impact-lab", mode=os.getenv("APP_MODE", "DEMO"), language="en")
            db.add(school)
            db.add(SchoolSetting(school_id=school.id, settings={"school_name": school.name, "urgent_help_notice": "ImpactOS is not an emergency channel. Contact the school's designated safeguarding team for urgent help.", "private_report_owner_role": "ADMIN", "allowed_categories": ["ACADEMICS", "CAMPUS", "WELLBEING", "ENVIRONMENT"], "retention_reference": "To be confirmed with Pilar", "publication_policy": "School-only during closed alpha"}))
        demo_users = [
            ("user-student", "student@demo.local", "Aisha Student", "STUDENT"),
            ("user-leader", "leader@demo.local", "Rafi Project Leader", "STUDENT_LEADER"),
            ("user-mentor", "mentor@demo.local", "Ms. Rani Mentor", "MENTOR"),
            ("user-osis", "osis@demo.local", "Dimas OSIS Reviewer", "OSIS"),
            ("user-moderator", "moderator@demo.local", "Nadia Moderator", "MODERATOR"),
            ("user-admin", "admin@demo.local", "Pilar Administrator", "ADMIN"),
        ]
        users: dict[str, User] = {}
        for uid, email, name, role in demo_users:
            user = db.get(User, uid)
            if not user:
                user = User(id=uid, school_id=school.id, email=email, display_name=name, role=role, password_hash=hash_password(DEMO_PASSWORD), active=True)
                db.add(user)
            users[email] = user
        db.flush()
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
        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_demo()


@app.get(f"{API}/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "impactos-api", "mode": os.getenv("APP_MODE", "DEMO"), "synthetic_data": True}


@app.post(f"{API}/auth/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    session, csrf = create_session(user)
    response.set_cookie(SESSION_COOKIE, session, httponly=True, samesite="lax", secure=False, max_age=60 * 60 * 12)
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, samesite="lax", secure=False, max_age=60 * 60 * 12)
    audit(db, user, "LOGIN", "USER", user.id)
    db.commit()
    return {"user": user_dict(user), "mode": os.getenv("APP_MODE", "DEMO"), "synthetic_data": True}


@app.post(f"{API}/auth/logout", dependencies=[Depends(require_csrf)])
def logout(response: Response, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    audit(db, actor, "LOGOUT", "USER", actor.id)
    db.commit()
    response.delete_cookie(SESSION_COOKIE)
    response.delete_cookie(CSRF_COOKIE)
    return {"status": "logged_out"}


@app.get(f"{API}/me", response_model=UserRead)
def me(actor: User = Depends(get_current_user)) -> User:
    return actor


@app.get(f"{API}/dashboard")
def dashboard(actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    school = db.get(School, actor.school_id)
    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.school_id == actor.school_id)).all()
    research = db.scalars(select(ResearchProject).where(ResearchProject.school_id == actor.school_id)).all()
    projects = db.scalars(select(ImpactProject).where(ImpactProject.school_id == actor.school_id)).all()
    private_count = db.scalar(select(func.count()).select_from(ProblemReport).where(ProblemReport.school_id == actor.school_id, ProblemReport.status == "PRIVATE_REVIEW")) or 0
    review_count = db.scalar(select(func.count()).select_from(ResearchProject).where(ResearchProject.school_id == actor.school_id, ResearchProject.status == "MENTOR_REVIEW")) or 0
    notifications = db.scalars(select(Notification).where(Notification.user_id == actor.id, Notification.read.is_(False)).order_by(Notification.created_at.desc()).limit(6)).all()
    next_actions: list[dict[str, str]] = []
    if actor.role == "MENTOR":
        next_actions = [{"title": "Review research plans", "detail": f"{review_count} plan(s) need a decision", "href": "/mentor"}]
    elif actor.role in {"MODERATOR", "ADMIN"}:
        next_actions = [{"title": "Restricted moderation queue", "detail": f"{private_count} private report(s)", "href": "/moderation"}]
    elif actor.role == "OSIS":
        next_actions = [{"title": "Review validated problems", "detail": f"{sum(1 for c in clusters if c.status == 'VALIDATED')} validated cluster(s)", "href": "/osis"}]
    else:
        next_actions = [{"title": "Continue the evidence-to-impact loop", "detail": "Report a measurable problem or open your active project.", "href": "/problems/new"}]
    return {"school": {"name": school.name if school else "Pilar Impact Lab", "language": school.language if school else "en"}, "mode": os.getenv("APP_MODE", "DEMO"), "synthetic_data": True, "role": actor.role, "counts": {"clusters": len(clusters), "research": len(research), "projects": len(projects), "private_reviews": private_count, "mentor_reviews": review_count}, "next_actions": next_actions, "notifications": [{"id": n.id, "title": n.title, "message": n.message, "created_at": dt(n.created_at)} for n in notifications]}


@app.get(f"{API}/problem-reports")
def list_reports(actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    reports = db.scalars(select(ProblemReport).where(ProblemReport.school_id == actor.school_id).order_by(ProblemReport.updated_at.desc())).all()
    if actor.role not in {"MODERATOR", "ADMIN"}:
        reports = [r for r in reports if r.author_id == actor.id or r.status in {"PUBLISHED", "MERGED"}]
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
    if report.author_id != actor.id and actor.role not in {"MODERATOR", "ADMIN"}:
        raise HTTPException(403, "Only the author or a moderator can edit this report.")
    if report.status not in {"DRAFT", "CHANGES_REQUESTED"} and actor.role not in {"MODERATOR", "ADMIN"}:
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
    if report.status == "PRIVATE_REVIEW" and actor.id != report.author_id and actor.role not in {"MODERATOR", "ADMIN"}:
        raise HTTPException(404, "Report not found.")
    return report_dict(db, report, actor)


@app.post(f"{API}/problem-reports/{{report_id}}/submit", dependencies=[Depends(require_csrf)])
def submit_report(report_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report:
        raise HTTPException(404, "Report not found.")
    require_same_school(actor, report.school_id)
    if report.author_id != actor.id and actor.role not in {"MODERATOR", "ADMIN"}:
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
def list_clusters(actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    clusters = db.scalars(select(ProblemCluster).where(ProblemCluster.school_id == actor.school_id).order_by(ProblemCluster.updated_at.desc())).all()
    return [cluster_dict(db, cluster, actor) for cluster in clusters]


@app.get(f"{API}/problem-clusters/{{cluster_id}}")
def get_cluster(cluster_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    return cluster_dict(db, cluster, actor)


@app.post(f"{API}/problem-clusters/{{cluster_id}}/signals", dependencies=[Depends(require_csrf)])
def add_signal(cluster_id: str, payload: SignalCreate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
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
def delete_signal(cluster_id: str, signal_type: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    signal = db.scalar(select(ProblemSignal).where(ProblemSignal.cluster_id == cluster_id, ProblemSignal.user_id == actor.id, ProblemSignal.signal_type == signal_type))
    if signal:
        db.delete(signal)
        audit(db, actor, "SIGNAL_REMOVED", "PROBLEM_CLUSTER", cluster_id, {"signal_type": signal_type})
        db.commit()
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    return cluster_dict(db, cluster, actor)


@app.post(f"{API}/problem-clusters/{{cluster_id}}/evidence", dependencies=[Depends(require_csrf)])
def add_evidence(cluster_id: str, payload: EvidenceCreate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
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
def moderation_queue(actor: User = Depends(require_roles("MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    reports = db.scalars(select(ProblemReport).where(ProblemReport.school_id == actor.school_id, ProblemReport.status.in_(["PRIVATE_REVIEW", "MODERATION_REVIEW"])).order_by(ProblemReport.created_at)).all()
    return {"private": [report_dict(db, r, actor) for r in reports if r.status == "PRIVATE_REVIEW"], "visibility": [report_dict(db, r, actor) for r in reports if r.status == "MODERATION_REVIEW"], "duplicate_candidates": [{"report_id": r.id, "candidates": []} for r in reports]}


@app.post(f"{API}/moderation/problem-reports/{{report_id}}/visibility-decision", dependencies=[Depends(require_csrf)])
def visibility_decision(report_id: str, payload: DecisionRequest, actor: User = Depends(require_roles("MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    report = db.get(ProblemReport, report_id)
    if not report:
        raise HTTPException(404, "Report not found.")
    require_same_school(actor, report.school_id)
    decision = payload.decision.upper()
    if decision == "PUBLISH":
        if not report.cluster_id:
            cluster = ProblemCluster(id=new_id(), school_id=actor.school_id, title=report.title, summary=report.description, category=report.category, scope=report.scope, status="GATHERING_EVIDENCE")
            db.add(cluster)
            db.flush()
            report.cluster_id = cluster.id
        target = "PUBLISHED"
    elif decision == "KEEP_PRIVATE":
        target = "PRIVATE_REVIEW"
    elif decision == "ARCHIVE":
        target = "ARCHIVED"
    else:
        raise HTTPException(422, "Decision must be PUBLISH, KEEP_PRIVATE, or ARCHIVE.")
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
def official_update(cluster_id: str, payload: OfficialUpdateCreate, actor: User = Depends(require_roles("OSIS", "MODERATOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
    cluster = db.get(ProblemCluster, cluster_id)
    if not cluster:
        raise HTTPException(404, "Problem cluster not found.")
    require_same_school(actor, cluster.school_id)
    update = OfficialUpdate(id=new_id(), school_id=actor.school_id, cluster_id=cluster_id, author_id=actor.id, status=payload.status, message=payload.message)
    db.add(update)
    cluster.updated_at = datetime.utcnow()
    for report in db.scalars(select(ProblemReport).where(ProblemReport.cluster_id == cluster_id)).all():
        notify(db, report.author_id, "Official update", payload.message)
    audit(db, actor, "OFFICIAL_UPDATE_PUBLISHED", "PROBLEM_CLUSTER", cluster_id, {"status": payload.status})
    db.commit()
    return cluster_dict(db, cluster, actor)


@app.post(f"{API}/research-projects", dependencies=[Depends(require_csrf)])
def create_research(payload: ResearchCreate, actor: User = Depends(require_roles("STUDENT", "STUDENT_LEADER", "MENTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict[str, Any]:
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
    if actor.role == "MENTOR":
        query = query.where(ResearchProject.mentor_id == actor.id)
    elif actor.role in {"STUDENT", "STUDENT_LEADER"}:
        query = query.where(ResearchProject.leader_id == actor.id)
    return [research_dict(db, r) for r in db.scalars(query.order_by(ResearchProject.updated_at.desc())).all()]


@app.get(f"{API}/research-projects/{{research_id}}")
def get_research(research_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    research = db.get(ResearchProject, research_id)
    if not research:
        raise HTTPException(404, "Research project not found.")
    require_same_school(actor, research.school_id)
    if actor.role in {"STUDENT", "STUDENT_LEADER"} and actor.id not in {research.leader_id}:
        raise HTTPException(403, "This research workspace is restricted.")
    if actor.role == "MENTOR" and research.mentor_id != actor.id:
        raise HTTPException(403, "This research workspace is not assigned to you.")
    return research_dict(db, research)


@app.put(f"{API}/research-projects/{{research_id}}/plan", dependencies=[Depends(require_csrf)])
def update_plan(research_id: str, payload: ResearchPlanUpdate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    research = db.get(ResearchProject, research_id)
    if not research:
        raise HTTPException(404, "Research project not found.")
    require_same_school(actor, research.school_id)
    if actor.id != research.leader_id and actor.role not in {"MENTOR", "ADMIN"}:
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
    if actor.id != research.leader_id and actor.role not in {"MENTOR", "ADMIN"}:
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
    db.add(Review(id=new_id(), school_id=actor.school_id, entity_type=entity_type, entity_id=entity_id, reviewer_id=actor.id, decision=decision, reason=reason))
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
    if actor.id != survey.created_by and actor.role not in {"MENTOR", "ADMIN"}:
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
    if actor.role == "MENTOR":
        query = query.where(ImpactProject.mentor_id == actor.id)
    elif actor.role in {"STUDENT", "STUDENT_LEADER"}:
        query = query.where(ImpactProject.leader_id == actor.id)
    return [impact_dict(db, p) for p in db.scalars(query.order_by(ImpactProject.updated_at.desc())).all()]


@app.get(f"{API}/impact-projects/{{project_id}}")
def get_impact(project_id: str, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if actor.role in {"STUDENT", "STUDENT_LEADER"} and actor.id != project.leader_id:
        raise HTTPException(403, "This impact project is restricted.")
    if actor.role == "MENTOR" and project.mentor_id != actor.id:
        raise HTTPException(403, "This impact project is not assigned to you.")
    return impact_dict(db, project)


@app.patch(f"{API}/impact-projects/{{project_id}}", dependencies=[Depends(require_csrf)])
def update_impact(project_id: str, payload: ImpactUpdate, actor: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    project = db.get(ImpactProject, project_id)
    if not project:
        raise HTTPException(404, "Impact project not found.")
    require_same_school(actor, project.school_id)
    if actor.id != project.leader_id and actor.role not in {"MENTOR", "ADMIN"}:
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
    if actor.id != project.leader_id and actor.role not in {"MENTOR", "ADMIN"}:
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
    if actor.id != project.leader_id and actor.role not in {"MENTOR", "ADMIN"}:
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
    if actor.id != project.leader_id and actor.role not in {"MENTOR", "ADMIN"}:
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
    if actor.id != project.leader_id and actor.role not in {"MENTOR", "ADMIN"}:
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
    if actor.role in {"STUDENT", "STUDENT_LEADER"} and actor.id != project.leader_id:
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
    if actor.id != project.leader_id and actor.role not in {"MENTOR", "ADMIN"}:
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


@app.get(f"{API}/mentor/attention")
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


@app.get(f"{API}/admin/audit-logs")
def audit_logs(actor: User = Depends(require_roles("ADMIN", "MODERATOR")), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(AuditLog).where(AuditLog.school_id == actor.school_id).order_by(AuditLog.created_at.desc()).limit(100)).all()
    return [{"id": row.id, "actor_id": row.actor_id, "action": row.action, "entity_type": row.entity_type, "entity_id": row.entity_id, "metadata": row.metadata_safe, "created_at": dt(row.created_at)} for row in rows]


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
