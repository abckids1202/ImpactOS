from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    role: str
    school_id: str
    status: str = "ACTIVE"


class AuthMeResponse(BaseModel):
    user: dict[str, Any]
    memberships: list[dict[str, Any]]


class ProblemCreate(BaseModel):
    title: str = Field(min_length=5, max_length=240)
    description: str = Field(min_length=20)
    affected_group: str = Field(min_length=2)
    scope: str = Field(min_length=2)
    category: str = "OTHER"
    frequency: str = ""
    severity: str = "MEDIUM"
    visibility: Literal["SCHOOL_NAMED", "SCHOOL_ANONYMOUS", "PRIVATE_REVIEW"] = "SCHOOL_NAMED"


class ProblemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    affected_group: str | None = None
    scope: str | None = None
    category: str | None = None
    frequency: str | None = None
    severity: str | None = None
    visibility: str | None = None


class SignalCreate(BaseModel):
    signal_type: Literal["AFFECTS_ME", "HAS_EVIDENCE", "WANTS_TO_INVESTIGATE", "WANTS_TO_HELP"]


class EvidenceCreate(BaseModel):
    source: str = Field(min_length=2)
    evidence_type: str = "OBSERVATION"
    observation_date: str | None = None
    relevance: str = ""
    visibility: str = "TEAM"
    file_name: str | None = None


class DecisionRequest(BaseModel):
    decision: str
    reason: str = Field(min_length=3)


class MergeRequest(BaseModel):
    cluster_id: str
    reason: str = Field(min_length=3)


class OfficialUpdateCreate(BaseModel):
    status: str
    message: str = Field(min_length=3)


class PriorityRequest(BaseModel):
    priority: Literal["LOW", "MEDIUM", "HIGH", "URGENT"]
    rationale: str = Field(min_length=3, max_length=1000)


class ResearchCreate(BaseModel):
    cluster_id: str
    title: str = Field(min_length=5, max_length=240)


class ResearchPlanUpdate(BaseModel):
    question: str = ""
    question_type: str = "descriptive"
    hypothesis: str = ""
    population: str = ""
    variables: list[dict[str, Any]] = Field(default_factory=list)
    method: str = ""
    sampling: str = ""
    data_collection: str = ""
    ethics: str = ""
    limitations: str = ""
    conclusion_boundary: str = ""


class SurveyCreate(BaseModel):
    research_id: str
    title: str = Field(min_length=5)
    purpose: str = ""
    privacy_mode: Literal["ANONYMOUS", "AUTHENTICATED"] = "ANONYMOUS"
    one_response: bool = True


class SurveyQuestionCreate(BaseModel):
    question_type: Literal["MCQ", "LIKERT", "NUMBER", "SHORT_TEXT"]
    prompt: str = Field(min_length=3)
    options: list[str] = Field(default_factory=list)
    required: bool = True


class SurveyResponseCreate(BaseModel):
    answers: dict[str, Any]
    idempotency_key: str = Field(min_length=8, max_length=120)


class ImpactCreate(BaseModel):
    research_id: str | None = None
    cluster_id: str
    title: str = Field(min_length=5, max_length=240)


class ImpactUpdate(BaseModel):
    target_users: str | None = None
    intervention: str | None = None
    theory_of_change: str | None = None
    risks: str | None = None
    resources: str | None = None


class MetricCreate(BaseModel):
    name: str = Field(min_length=3)
    description: str = ""
    unit: str = Field(min_length=1)
    direction: str = "DECREASE"
    collection_method: str = ""
    target: float | None = None
    is_primary: bool = False


class ObservationCreate(BaseModel):
    phase: Literal["BASELINE", "DURING", "POST", "FOLLOW_UP"]
    value: float
    observed_on: str
    sample_size: int | None = None
    notes: str = ""


class ReportUpdate(BaseModel):
    content: dict[str, Any]


class InvitationCreate(BaseModel):
    email: str
    role: Literal["STUDENT", "STUDENT_LEADER", "MENTOR", "OSIS"] = "STUDENT"
    roles: list[str] | None = None
    expires_in_days: int = Field(default=7, ge=1, le=30)


class InvitationAccept(BaseModel):
    email: str | None = None
    display_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=10, max_length=128)
    password_confirmation: str | None = None
    accepted_rules: bool = True


class ActivationEmailRequest(BaseModel):
    email: str


class PasswordForgotRequest(BaseModel):
    email: str


class PasswordResetRequest(BaseModel):
    token: str
    password: str = Field(min_length=10, max_length=128)


class RoleAssignmentRequest(BaseModel):
    roles: list[str] = Field(min_length=1)


class TaskUpdate(BaseModel):
    status: Literal["TODO", "IN_PROGRESS", "BLOCKED", "COMPLETED"]


class FeedbackCreate(BaseModel):
    category: Literal["BROKEN", "CONFUSING", "SUGGESTION", "ACCESSIBILITY", "OTHER"]
    description: str = Field(min_length=10, max_length=4000)
    severity: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    allow_contact: bool = False
    route: str = Field(default="", max_length=255)
    user_role: str = Field(default="", max_length=80)
    browser: str = Field(default="", max_length=120)
    screen_size: str = Field(default="", max_length=40)
    app_version: str = Field(default="0.1.0", max_length=40)
