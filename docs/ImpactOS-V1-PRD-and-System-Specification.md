ImpactOS V1 — Product Requirements Document and System Specification

Pilot name: Pilar Impact Lab
Product name: ImpactOS
Pilot institution: Sekolah Pilar Indonesia
Document status: Planning baseline / pre-development
Version: 1.0
Date: 23 August 2026
Primary owner: Student product team

1. Executive summary

ImpactOS is a school platform that helps students turn observations about real problems into evidence-backed research, practical interventions, and measurable impact.

The Pilar pilot will be branded Pilar Impact Lab. It unifies three concepts as stages of one continuous system:

PilarVoice: discover and validate problems.

ResearchOS: investigate causes and collect evidence.

ImpactForge: build an intervention and measure whether it worked.

The product is not a complaint board, a generic project-management tool, or an AI chatbot. Its defining loop is:

flowchart TD
    A["Discover a problem"] --> B["Validate with people and evidence"]
    B --> C["Research causes and scope"]
    C --> D["Propose an intervention"]
    D --> E["Build and run a pilot"]
    E --> F["Measure before and after"]
    F --> G["Review and publish impact"]

The first version must prove that one student concern can travel through this full loop without leaving the platform.

2. Product vision

Vision statement

Enable every student-led school project to begin with a real need, develop through responsible inquiry, and end with evidence of what changed.

Product promise

Find something worth fixing, understand it, act on it, and show whether the action helped.

Pilot hypothesis

If students receive a structured, AI-assisted path from problem discovery to impact measurement, then their projects will become more specific, evidence-based, measurable, and useful to the school community.

Why this matters at Pilar

Student observations often disappear into conversations, forms, or disconnected group chats. At the same time, student projects may begin with a solution idea before the underlying need is validated. Pilar Impact Lab connects school concerns, research, projects, mentor feedback, and official responses into one traceable process.

3. Problem statement

Current situation

Students notice problems but lack a structured place to document them.

Similar concerns are submitted repeatedly without being connected.

Popularity can be mistaken for importance when feedback is reduced to likes or upvotes.

Student projects can begin without a validated problem, baseline, or success metric.

Evidence, surveys, project tasks, mentor comments, and final reports live in different tools.

Teachers and OSIS cannot easily see which projects are stalled or which concerns have strong evidence.

School responses are difficult to follow over time.

Desired situation

Every serious initiative can show a chain of reasoning:

real problem → affected people → evidence → research → intervention → result → limitations → next action

Core product question

Can ImpactOS improve the quality and measurability of student-led projects without creating excessive administrative work for students or mentors?

4. Goals, non-goals, and principles

V1 goals

Let students safely report and validate school or community problems.

Connect duplicate reports into shared problem clusters.

Help students create a defensible research question and plan.

Let students gather evidence through a small built-in survey tool and uploaded evidence.

Convert validated research into an intervention project.

Require baseline and success metrics before the intervention begins.

Give mentors an efficient review and feedback workflow.

Let OSIS or school reviewers communicate an official status or response.

Generate a traceable final impact report.

Protect student privacy and ensure AI never makes disciplinary or policy decisions.

Non-goals for V1

A public social network or discussion forum.

A replacement for safeguarding, emergency, or formal disciplinary reporting.

A full learning-management system.

A full Jira-like project-management suite.

A mobile application.

Custom-trained NLP models.

Automatic school policy decisions.

Advanced causal inference or a promise that an intervention caused an observed change.

Public leaderboards, badges, popularity rankings, or gamification.

Complex budget, procurement, or inventory management.

Cross-school marketplace or national deployment.

Product principles

Evidence over popularity: use structured signals, not upvotes.

One connected journey: Voice, Research, and Forge must share the same entities and history.

Human authority: AI suggests, flags, and explains; people approve and decide.

Privacy by default: collect the minimum data needed.

Visible reasoning: users should see why an AI or rule-based warning appeared.

Honest measurement: distinguish observation, association, and causation.

Simple enough to finish: every screen must serve the core loop.

5. Target users and jobs to be done

5.1 Student contributor

Primary job: “When I notice a recurring problem, help me describe it clearly, see whether others experience it, and contribute evidence or help.”

Can:

Submit a problem.

Choose public, anonymous-public, or private-review visibility.

Respond to AI clarification questions.

Signal “This affects me,” “I have evidence,” “I want to investigate,” or “I want to help.”

Follow a problem cluster and receive updates.

Add evidence where permitted.

Join a research or intervention team by invitation.

5.2 Student project leader

Primary job: “Help my team investigate a problem, build a realistic intervention, and prove what happened.”

Can:

Create and manage research plans.

Create surveys and review results.

Link claims to evidence.

Propose an intervention.

Invite team members.

Manage lightweight tasks and milestones.

Define impact metrics and record observations.

Request mentor reviews.

Submit a final impact report.

5.3 Teacher or mentor

Primary job: “Show me where student teams need my judgment so I do not have to read every page every day.”

Can:

Review research plans, surveys, interventions, and impact reports.

Approve, request changes, or comment.

See methodology and ethics warnings.

See projects that are stale, late, or missing baselines.

View only the data permitted for the assigned project.

5.4 OSIS reviewer

Primary job: “Help us identify recurring student needs, decide what deserves action, and communicate progress transparently.”

Can:

Review non-sensitive school-wide clusters.

Set priority factors with a written rationale.

Link an OSIS initiative to a problem.

Publish official status updates.

View aggregate, non-identifying trends.

5.5 School administrator or moderator

Primary job: “Keep the platform safe, correctly configured, and accountable.”

Can:

Manage users, roles, school structure, categories, and workflow settings.

Review sensitive or flagged reports.

Decide visibility and merging.

Assign mentors or reviewers.

View audit logs.

Disable content or accounts according to school policy.

Configure data retention and export.

6. Scope decision: V1 pilot

The source concept contains enough features for several releases. V1 is therefore defined as a pilot-ready vertical slice, not the final platform.

Included in V1

Foundation

Invite-based or school-managed authentication.

Role-based access control.

School, grade, class, and category configuration.

Notifications inside the app.

File upload with type and size restrictions.

Audit log for important actions.

Voice

Problem-report form.

AI-assisted clarification.

Sensitive-content routing.

Duplicate suggestions using embeddings.

Moderator-controlled problem clusters.

Four structured student signals.

Evidence attachments.

Status timeline and official response.

Research

Research workspace linked to one problem cluster.

Research question, hypothesis, population, variables, method, sampling, ethics, limitations, and conclusion boundaries.

Deterministic methodology warnings.

Mentor review.

Survey builder with only multiple choice, Likert scale, number, and short text.

Anonymous or authenticated school-only survey collection.

Counts, percentages, mean, median, and simple distributions.

CSV export for authorized researchers.

Evidence library and claim-to-evidence links.

Impact project

Convert approved research into an intervention proposal.

Theory-of-change builder.

Team, tasks, milestones, and updates.

Mentor review.

One primary and up to three secondary metrics.

Baseline, during, post, and follow-up observations.

Before-versus-after display with careful language.

Structured final impact report.

Governance

Private review queue.

Manual merge and unmerge of duplicate reports.

Official status and response history.

Basic mentor, OSIS, and admin dashboards.

Deferred until after the pilot

Open-ended response clustering with HDBSCAN or KMeans.

Dataset workspace for arbitrary XLSX/CSV analysis.

Direct interviews and consent-management workflows.

Advanced cross-tabulation, correlations, or confidence intervals.

Rich-text collaborative editing.

Public discussions or comments on problem pages.

Email, push, or chat integrations.

Automatic intervention recommendations.

Custom model training.

Multi-school administration UI.

Native mobile app.

V1 sizing rule

If a feature does not help complete or safeguard the core loop, it should not enter the pilot backlog.

7. End-to-end workflow

7.1 Happy path

Stage

Primary actor

Required action

System output

Human checkpoint

Discover

Student

Submit a problem

Structured draft and sensitivity check

Student confirms AI interpretation

Moderate

Moderator

Review visibility and possible duplicate

Published report or private routing

Moderator decides visibility/merge

Validate

Students

Add structured signals and evidence

Affected count and evidence set

Reviewer decides whether validation is sufficient

Research

Student leader

Create research plan

Research workspace and warnings

Mentor approves or requests changes

Collect

Research team

Publish survey/add evidence

Response dataset and evidence library

Survey approval if required

Analyze

Research team

Review basic analysis and claims

Findings with limitation warnings

Mentor accepts research completion

Propose

Student leader

Design intervention and metrics

Theory of change and project proposal

Mentor/authorized reviewer approves

Build

Project team

Complete tasks and milestones

Progress timeline

Mentor monitors exceptions

Measure

Project team

Record post-intervention observations

Before/after result

System prevents unsupported causal wording

Review

Mentor/reviewer

Review impact report

Approved or changes requested

Human signs off

Impact

Authorized publisher

Publish result and official response

Shareable internal impact page

Publication permission checked

7.2 Example journey

A Grade 10 student reports that major assignments are repeatedly due within the same three-day periods.

The AI asks for the affected grade, approximate frequency, and possible evidence.

The system finds similar reports. A moderator merges the new report into Assessment Workload Concentration.

Other students select “This affects me”; some add timetable screenshots or dates.

A student leader selects “Investigate this problem” and creates a descriptive research question.

A mentor reviews the sample, survey wording, privacy setting, and planned analysis.

The team gathers responses and analyzes assignment dates.

The evidence supports deadline concentration, but not a causal claim about academic performance.

The team proposes a shared assessment scheduling intervention and defines a baseline before rollout.

After the pilot, the team records the post-intervention measurement.

ImpactOS reports the observed change, limitations, and evidence; it does not claim causality without an appropriate design.

The school publishes a response and next action.

7.3 Exception paths

Sensitive report: bypasses public feeds and enters private review.

Probable duplicate: the author can view suggestions, but only a moderator merges records.

Insufficient evidence: cluster remains in “Gathering evidence”; it cannot be marked validated without reviewer rationale.

Survey contains sensitive fields: publishing is blocked pending mentor/admin review.

Project lacks a baseline: intervention approval is blocked unless a reviewer records a justified exception.

AI unavailable: the user continues through the manual form; no core workflow is blocked.

Team becomes inactive: mentor dashboard shows a stale-project warning after a configurable interval.

Impact is negative or inconclusive: report still completes and must include what did not work.

8. Workflow states and transitions

8.1 Problem report states

DRAFT → SUBMITTED → PRIVATE_REVIEW or PUBLISHED → MERGED or ARCHIVED

Rules:

A sensitive report goes directly from SUBMITTED to PRIVATE_REVIEW.

MERGED reports remain readable by authorized users and retain their original author and evidence.

Only moderators can publish private reports, merge reports, unmerge reports, or archive reports.

8.2 Problem cluster states

NEW → GATHERING_EVIDENCE → VALIDATED → UNDER_INVESTIGATION → ACTION_PLANNED → ACTION_UNDERWAY → RESOLVED → IMPACT_MEASURED → CLOSED

Rules:

Status changes require a reason and create an audit event.

VALIDATED is a human decision, not an AI threshold.

A cluster may return to an earlier state with a written reason.

“Resolved” and “impact measured” are separate states.

8.3 Research states

DRAFT → MENTOR_REVIEW → CHANGES_REQUESTED or APPROVED → COLLECTING → ANALYZING → COMPLETED → ARCHIVED

Rules:

Data collection cannot begin until required review is approved.

Changes to an approved survey create a new survey version and may require reapproval.

A completed research project preserves its plan and evidence snapshot.

8.4 Survey states

DRAFT → REVIEW_REQUIRED → APPROVED → OPEN → CLOSED → ARCHIVED

Rules:

Responses are accepted only while OPEN and within the configured time window.

Anonymous surveys never expose an identity mapping to the student researcher.

Closing a survey is reversible only by an authorized reviewer, with an audit reason.

8.5 Impact project states

DRAFT → REVIEW → CHANGES_REQUESTED or APPROVED → ACTIVE → PAUSED or COMPLETED → IMPACT_REVIEW → PUBLISHED or ARCHIVED

Rules:

A project cannot become ACTIVE until its primary metric and baseline plan exist.

Completing tasks does not automatically mean the project achieved impact.

Publication requires final review and allowed visibility.

9. Functional requirements

Priority labels: P0 is required for the pilot, P1 is important if capacity allows, and P2 is later.

9.1 Authentication and accounts

ID

Requirement

Priority

Acceptance criterion

AUTH-01

Users sign in through an invitation or approved school account.

P0

Uninvited accounts cannot access protected routes.

AUTH-02

Every user has one or more role assignments scoped to the school.

P0

The API rejects actions outside the user's permissions.

AUTH-03

Admins can deactivate an account without deleting its authored records.

P0

Deactivated users cannot sign in; historical attribution remains.

AUTH-04

Student profiles store only necessary school information.

P0

No date of birth, home address, phone, or parent data is required.

9.2 Problem discovery and validation

ID

Requirement

Priority

Acceptance criterion

VOICE-01

Students can save and submit a report with title, description, affected group, category, scope, visibility, and attachments.

P0

Required fields validate on client and server.

VOICE-02

AI returns a structured interpretation and up to three useful clarification questions.

P0

Student can accept, edit, or ignore each suggestion.

VOICE-03

Sensitive reports are prevented from automatic public publication.

P0

Flagged reports appear only in the private review queue.

VOICE-04

The system presents likely duplicate clusters.

P0

Similarity is shown as a suggestion; no automatic merge occurs.

VOICE-05

Moderators can merge a report into a cluster and undo the merge.

P0

Original report and evidence remain intact after both operations.

VOICE-06

Students can add one of four structured signals once per report or cluster.

P0

Duplicate signals from the same account and type are prevented.

VOICE-07

Authorized users can add evidence with source, observation date, type, relevance, and visibility.

P0

Evidence metadata and file permissions are enforced.

VOICE-08

Problem pages show status, affected count, evidence count, linked research, linked projects, and response history.

P0

Counts match authorized underlying records.

9.3 Research workspace

ID

Requirement

Priority

Acceptance criterion

RES-01

A project leader can create one or more research investigations linked to a cluster.

P0

The link is visible from both entities.

RES-02

Research plans contain question, hypothesis, population, variables, method, sampling, ethics, limitations, and conclusion boundary.

P0

Missing required sections block mentor submission.

RES-03

AI can suggest descriptive, comparative, or associational questions.

P0

Suggestions remain editable and are labeled by question type.

RES-04

Deterministic rules flag selection bias, leading wording, double-barrelled questions, privacy risk, and unsupported causal claims.

P0

Each warning identifies the triggering text and a correction.

RES-05

Mentors can approve, request changes, and comment on a plan.

P0

The decision, author, time, and version are stored.

RES-06

Claims can be linked to evidence with a strength and note.

P1

Users can inspect all evidence supporting a claim.

9.4 Survey collection and analysis

ID

Requirement

Priority

Acceptance criterion

SUR-01

Leaders can create MCQ, Likert, number, and short-text questions.

P0

Questions can be reordered, required, edited, and removed in draft.

SUR-02

Surveys can be anonymous or authenticated and restricted by grade/class.

P0

Access and one-response rules are enforced server-side.

SUR-03

AI and deterministic checks review wording before publication.

P0

Critical privacy warnings block publish; other warnings require acknowledgement.

SUR-04

The system collects responses without exposing identities for anonymous surveys.

P0

Researcher exports contain no user identifier or reversible hash.

SUR-05

Results include response count, percentages, mean/median where valid, and distributions.

P0

Calculations are covered by automated tests against known fixtures.

SUR-06

Authorized users can export a CSV.

P1

Export obeys survey privacy and role settings.

9.5 Intervention and impact

ID

Requirement

Priority

Acceptance criterion

IMP-01

Approved research can be converted into an intervention project.

P0

Problem, research, and selected evidence links are preserved.

IMP-02

A proposal contains intervention, target group, theory of change, risks, resources, team, mentor, and timeline.

P0

Missing required fields block review submission.

IMP-03

Projects support lightweight tasks and milestones.

P0

Tasks have owner, status, due date, priority, and milestone.

IMP-04

A primary metric and baseline plan are required before approval.

P0

Approval endpoint rejects a project without both.

IMP-05

Users can record baseline, during, post, and follow-up observations with evidence.

P0

Every observation stores unit, date, phase, recorder, and optional evidence.

IMP-06

Result pages compare periods without automatically asserting causality.

P0

Generated wording uses “observed” unless the method supports a stronger claim.

IMP-07

The system generates an editable impact report.

P0

Report includes problem, evidence, research, intervention, implementation, results, limitations, failures, next steps, and appendix.

9.6 Review, governance, and transparency

ID

Requirement

Priority

Acceptance criterion

GOV-01

Authorized reviewers can publish official status updates.

P0

Updates are chronological and cannot be silently overwritten.

GOV-02

A private moderation queue shows sensitivity reason, reporter visibility choice, and review status.

P0

Only assigned roles can open private submissions.

GOV-03

Important mutations create audit events.

P0

Actor, action, entity, timestamp, and safe metadata are recorded.

GOV-04

Priority recommendations show reach, severity, frequency, evidence strength, trend, and actionability separately.

P1

Reviewer can override any recommendation with a reason.

GOV-05

The UI states that the platform is not an emergency channel.

P0

Notice appears on report creation and sensitive-report confirmation.

10. Role and permission matrix

Legend: C create, R read, U update, A approve/moderate, — no access. “Assigned” means the user is a member, mentor, or designated reviewer.

Resource/action

Student

Project leader

Assigned mentor

OSIS reviewer

Admin/moderator

Public problem reports

C/R/own U

C/R/own U

R

R

R/U/A

Private reports

C/own R

C/own R

Assigned R

— unless assigned

R/U/A

Problem clusters

R/signal

R/signal

R

R/U/A

R/U/A

Evidence

C/R allowed

C/R/U own

R/comment

R allowed

R/U/A

Research plan

Team R

C/R/U

Assigned R/U/A

Summary R

R/U/A

Survey draft

Team R

C/R/U

Assigned R/U/A

—

R/U/A

Anonymous responses

—

Aggregate R

Aggregate R

Aggregate only if authorized

Restricted aggregate R

Identified responses

—

Only if explicitly approved

Only if explicitly approved

—

Restricted as policy allows

Impact project

Team R

C/R/U

Assigned R/U/A

Summary R/U if owner

R/U/A

Official response

R

R

R

C/R/U/A

C/R/U/A

Audit log

—

—

Assigned entity history

Limited governance history

R

User/role management

—

—

—

—

C/R/U/A

Permission checks must exist in the backend. Hiding a button is not authorization.

11. Information architecture and page specification

11.1 Global navigation

Dashboard

Problems

Research

Projects

Notifications

Role workspace: Mentor, OSIS, or Admin when authorized

Profile and settings

11.2 Student dashboard

Purpose: show the next useful action, not generic statistics.

Sections:

Continue: drafts, assigned tasks, and requested changes.

Your projects: progress, next milestone, and mentor status.

Problems followed: current status and latest official update.

Research: response count and pending review.

Suggested action: one contextual card, such as “Add a baseline before the pilot.”

11.3 Problems index

Components:

Search.

Filters: category, scope, status, affected group, and updated date.

Sort: recently updated, most affected, strongest evidence, and school priority.

Cards show title, short summary, status, category, structured-signal counts, and latest update.

Primary action: Report a Problem.

No public popularity score should be displayed.

11.4 Report-a-problem flow

Use a four-step form:

Describe: title and description.

Scope: who is affected, category, frequency, severity, and visibility.

Support: attachments, observation dates, and available evidence.

Review: AI interpretation, clarification questions, duplicate suggestions, and safety notice.

The student must explicitly confirm the final content before submission.

11.5 Problem cluster page

Header:

Cluster title and concise neutral summary.

Current state and last update.

Category, scope, affected count, evidence count, and linked work.

Structured-signal buttons.

Tabs:

Overview

Reports

Evidence

Research

Projects

Updates

Impact

Sensitive source reports must never be exposed through the cluster page.

11.6 Research workspace

Left navigation:

Research question

Plan

Variables

Evidence and claims

Survey

Analysis

Ethics and limitations

Mentor review

Persistent header:

Linked problem.

Research status.

Completeness indicator based on required sections, not AI quality scoring.

Current warnings.

Submit-for-review action.

11.7 Survey builder

Three panes on desktop:

Question list and ordering.

Question editor.

Preview and review warnings.

Mobile/tablet can collapse these panes sequentially. Publication settings include audience, anonymity, authentication, one-response policy, open/close dates, and consent/introduction text.

11.8 Survey response page

School or project identity.

Purpose and estimated completion time.

Privacy/anonymity explanation.

Questions.

Confirmation before submit.

Completion receipt with no sensitive response recap.

11.9 Analysis page

Total valid responses.

Missing-response count by question.

Chart appropriate to each question type.

Summary statistics only where mathematically valid.

Filters permitted only when privacy thresholds are met.

Methodology and interpretation warnings.

Export action for authorized roles.

11.10 Impact project workspace

Tabs:

Overview

Theory of change

Team

Tasks

Milestones

Evidence

Metrics

Updates

Mentor review

Impact report

The overview emphasizes the next milestone, missing requirements, risks, and recent activity.

11.11 Mentor workspace

Queues:

Needs review.

Changes resubmitted.

Missing metric or baseline.

Ethics/privacy warning.

Due soon.

No update for configurable number of days.

Each item must explain why it appears in the queue.

11.12 OSIS workspace

Emerging non-sensitive problems.

Problems awaiting organizational response.

Active OSIS interventions.

Problems with strong evidence but no action.

Official-update composer.

Aggregate category and status trends.

11.13 Admin workspace

Users and roles.

Categories and school structure.

Private review queue.

Merge suggestions.

Workflow configuration.

Audit log.

Data retention/export controls.

System health and AI failure rate.

12. Data model

12.1 Modeling decisions

Separate raw problem reports from curated problem clusters.

Add school_id to core records even though the pilot is single-school; this prevents a costly redesign later.

Treat reviews as versioned decisions, not a mutable comment field.

Store survey definitions and approved versions separately from responses.

Keep anonymous response identity out of the researcher-facing data model.

Store AI outputs as suggestions with provider/model/version metadata and user decision, not as canonical truth.

Use soft archive for important records; avoid irreversible deletion through ordinary UI.

12.2 Core relationships

erDiagram
    SCHOOL ||--o{ USER : has
    USER ||--o{ PROBLEM_REPORT : submits
    PROBLEM_CLUSTER ||--o{ PROBLEM_REPORT : groups
    PROBLEM_CLUSTER ||--o{ RESEARCH_PROJECT : motivates
    RESEARCH_PROJECT ||--o{ SURVEY : contains
    RESEARCH_PROJECT ||--o{ EVIDENCE_ITEM : collects
    RESEARCH_PROJECT ||--o{ IMPACT_PROJECT : informs
    IMPACT_PROJECT ||--o{ IMPACT_METRIC : measures
    IMPACT_METRIC ||--o{ METRIC_OBSERVATION : records
    IMPACT_PROJECT ||--o{ TASK : organizes
    USER ||--o{ REVIEW : performs

12.3 Required tables

Identity and configuration

schools

users

memberships

roles

role_assignments

grades

classes

categories

Voice

problem_reports

problem_clusters

problem_cluster_memberships

problem_signals

official_updates

cluster_status_history

Research and evidence

research_projects

research_plan_versions

research_variables

claims

evidence_items

claim_evidence_links

surveys

survey_versions

survey_questions

survey_responses

survey_answers

Intervention and impact

impact_projects

project_members

tasks

milestones

impact_metrics

metric_observations

project_updates

impact_report_versions

Governance and platform

reviews

review_comments

notifications

files

ai_runs

moderation_flags

audit_logs

12.4 Important field examples

problem_reports

id, school_id, created_by

title, description

category_id, scope, affected_group

frequency, severity

visibility, status

sensitivity_level

submitted_at, created_at, updated_at

problem_clusters

id, school_id, title, neutral_summary

category_id, scope, status

priority_recommendation_json

embedding

created_by, created_at, updated_at

research_projects

id, school_id, problem_cluster_id, created_by

title, question, question_type, hypothesis

population, methodology_type, sampling_method

ethics_status, status

current_plan_version_id

created_at, updated_at

survey_responses

id, survey_version_id

respondent_token_hash only when enforcing one response

eligibility_snapshot_json

consent_recorded_at, submitted_at

no researcher-visible account identifier for anonymous surveys

impact_metrics

id, project_id, name, description

unit, direction, metric_type

is_primary, target_value

baseline_plan, collection_method

metric_observations

id, metric_id, value_numeric, value_text

phase, measurement_date

sample_size, evidence_id, recorded_by

notes, created_at

12.5 Data integrity constraints

Unique signal per user_id + cluster_id + signal_type.

Unique question position per survey version.

Only one primary metric per project.

Metric unit cannot change after baseline without creating a new metric version.

Approved plan and survey versions are immutable.

A report may belong to at most one active cluster.

Every status change requires a valid transition and actor permission.

Anonymous response exports cannot contain a user ID, email, display name, or reversible token.

13. Technical architecture

13.1 Recommended stack

Frontend

Vite

React

TypeScript

Tailwind CSS

React Router

TanStack Query

React Hook Form

Zod

Recharts

Zustand only for small client-side workflow state

Backend

FastAPI

Pydantic

SQLAlchemy 2

Alembic

PostgreSQL

pgvector

Redis and ARQ only when background jobs are needed

Analysis and NLP

pandas and NumPy for survey summaries

SciPy only for reviewed statistical features

sentence-transformers for similarity embeddings

provider-agnostic LLM adapter for structured assistance

Storage and deployment

S3-compatible object storage for files

Separate development, staging, and pilot production environments

Managed PostgreSQL with encrypted connections and automated backups

Error monitoring and structured logs with sensitive-field redaction

13.2 System context

flowchart TD
    U["Students and school staff"] --> W["React web application"]
    W --> A["FastAPI application"]
    A --> D["PostgreSQL and pgvector"]
    A --> O["Object storage"]
    A --> Q["Background jobs"]
    Q --> M["AI and embedding providers"]

13.3 Module boundaries

Backend modules:

auth and permissions

schools and users

problems and clustering

evidence

research and methodology

surveys and analysis

projects, tasks, and milestones

impact

reviews and governance

notifications

files

ai

audit

The modules communicate through explicit service interfaces. AI code must not be embedded inside route handlers.

13.4 API conventions

Base path: /api/v1.

JSON request and response bodies.

UUID identifiers.

Cursor pagination for feeds and logs.

Consistent error envelope with code, message, field errors, and request ID.

Optimistic concurrency or version field for edited plans and reports.

Idempotency keys for survey submission and high-value mutations.

OpenAPI generated from FastAPI and used to generate or validate frontend types.

13.5 Initial API groups

POST   /auth/login
POST   /auth/logout
GET    /me

POST   /problem-reports
GET    /problem-reports/{id}
POST   /problem-reports/{id}/submit
GET    /problem-clusters
GET    /problem-clusters/{id}
POST   /problem-clusters/{id}/signals
POST   /problem-clusters/{id}/evidence
POST   /moderation/problem-reports/{id}/decision
POST   /moderation/problem-reports/{id}/merge

POST   /research-projects
GET    /research-projects/{id}
PUT    /research-projects/{id}/plan
POST   /research-projects/{id}/submit-review
POST   /research-projects/{id}/claims

POST   /surveys
PUT    /surveys/{id}/draft
POST   /surveys/{id}/submit-review
POST   /surveys/{id}/publish
POST   /public/surveys/{code}/responses
GET    /surveys/{id}/analysis
GET    /surveys/{id}/export

POST   /impact-projects
GET    /impact-projects/{id}
POST   /impact-projects/{id}/tasks
POST   /impact-projects/{id}/milestones
POST   /impact-projects/{id}/metrics
POST   /impact-metrics/{id}/observations
POST   /impact-projects/{id}/submit-review
GET    /impact-projects/{id}/report

POST   /reviews
POST   /problem-clusters/{id}/official-updates
GET    /notifications
GET    /mentor/attention
GET    /osis/overview
GET    /admin/audit-logs

14. AI and rule architecture

14.1 V1 AI capabilities

Capability

Technique

Output

Human control

Problem extraction

LLM structured output

Category, claims, affected group, missing information

Author confirms

Sensitive-content flagging

Rules plus LLM classifier

Risk labels and reason

Moderator decides visibility

Duplicate suggestion

Embeddings plus vector similarity

Ranked cluster candidates

Moderator merges

Problem framing

LLM

More measurable wording and questions

Author edits/accepts

Research question helper

LLM plus templates

Descriptive/comparative/associational options

Student chooses; mentor reviews

Methodology checker

Deterministic rules first, LLM explanation second

Warnings and corrections

Mentor decides

Survey critic

Rules plus LLM

Wording, privacy, and bias warnings

Author edits; critical issues require review

Impact language guard

Rules plus LLM rewrite

Observational wording and limitations

Author and mentor approve

Mentor attention

Deterministic queries

Explainable risk reasons

Mentor prioritizes

14.2 AI execution contract

Every AI call must:

Use a versioned prompt template.

Send only the minimum relevant data.

Request a strict JSON schema.

Validate the response with Pydantic.

Reject or retry invalid output once.

Store model/provider, prompt version, duration, status, and a redacted input hash.

Display the result as a suggestion or warning.

Record whether the user accepted, edited, dismissed, or escalated it.

Fail safely without blocking the manual workflow.

14.3 Prohibited AI behavior

Automatically accuse, punish, rank, or label a student or staff member.

Decide whether a sensitive claim is true.

Publish a report or official response.

Merge clusters without review.

Invent evidence, survey responses, citations, or results.

Change a research plan, metric, or report silently.

Claim causation based only on before/after observation.

Train on student content without an explicit future governance decision.

14.4 Duplicate-engine approach

Normalize the title and description.

Create an embedding asynchronously.

Search active clusters within the same school and compatible category.

Combine semantic similarity with simple metadata compatibility.

Return up to three candidates with a short explanation.

Let the author indicate whether any match seems relevant.

Let a moderator make the final merge decision.

Thresholds must be tuned on synthetic and pilot-reviewed examples. A low-confidence result should display no suggestion rather than a forced match.

14.5 Deterministic methodology rules for V1

Initial rule set should cover:

Research question is too broad or contains multiple outcomes.

Population is missing or inconsistent with survey audience.

Variable lacks an operational definition.

Sample includes only a convenience subgroup but claims to represent the school.

Survey question is leading, loaded, double-barrelled, ambiguous, or lacks a neutral option.

Sensitive personal information is requested without justification.

Analysis uses a mean for an unsuitable category.

Conclusion exceeds the observed population.

Correlation or before/after change is described as causation.

Primary metric was created after intervention data was recorded.

Each rule has rule_id, severity, trigger, explanation, suggested correction, applicable entity, and version.

15. Privacy, safety, and governance

15.1 Data minimization

V1 should not require:

Date of birth.

Home address.

Personal phone number.

Parent information.

Government identifiers.

Medical or disciplinary records.

School identity is used only for access, role, grade/class eligibility, authorship where non-anonymous, and one-response enforcement where configured.

15.2 Sensitive-report handling

Potential bullying, harassment, abuse, self-harm, mental-health crisis, personal accusation, or individual staff/student complaint must enter a restricted review path. The platform should show the school's designated urgent-help route and state that ImpactOS is not monitored as an emergency channel.

AI only flags; trained school staff decide what happens next according to school policy.

15.3 Survey privacy

Anonymous is the default recommended setting.

Researchers must justify identifiable collection.

Respondents see purpose, data use, visibility, and anonymity before starting.

Authorized researchers see only what the approved design permits.

Small subgroup filters should be suppressed when they risk identification.

Free-text exports require an additional warning because responses may self-identify.

15.4 File security

Allowlist file types.

Enforce size limits.

Rename objects to generated IDs.

Scan files before making them available.

Use short-lived authorized download links.

Remove embedded metadata where appropriate for publicly visible images.

Never trust user-provided filenames or MIME types.

15.5 Audit events

At minimum log:

Role and account changes.

Private-report access and decisions.

Publish/unpublish actions.

Cluster merge/unmerge.

Review decisions.

Survey open/close and export.

Metric or baseline changes.

Official response publication.

Data export and administrative archive actions.

Do not put raw sensitive text, passwords, tokens, or full survey responses in logs.

15.6 Policy decisions required before pilot

The school must designate:

Who monitors private reports.

The urgent safeguarding route shown in the app.

Who may view identified survey data.

Minimum consent and ethics requirements.

Content retention duration.

Who can publish official responses.

Who owns moderation and appeals.

When project or impact pages may be shared outside the school.

16. Non-functional requirements

Security

Server-side permission checks on every protected operation.

Passwords hashed with an accepted adaptive password hash if local credentials are used.

Secure, HTTP-only session cookies or short-lived access tokens with safe refresh handling.

Rate limiting on authentication, survey submission, uploads, and AI endpoints.

CSRF protection when cookie-based authentication is used.

Secrets stored outside source control.

Dependency and container scanning in CI.

Reliability

Core manual flows remain available when AI providers fail.

Database migrations are reversible in staging and backed up before production changes.

Background jobs are retryable and idempotent.

Survey submission prevents accidental duplicates.

Daily backup during the pilot with a tested restore procedure.

Performance targets for the pilot

Standard authenticated page API: p95 below 800 ms under pilot load, excluding AI.

Feed/search response: p95 below 1.5 seconds.

Survey submission: acknowledged below 1 second in normal conditions.

AI suggestions: target below 10 seconds; show progress and permit manual continuation.

Initial responsive page load on school Wi-Fi: target below 3 seconds after authentication.

Accessibility and usability

Keyboard-accessible forms and navigation.

Visible focus states.

Proper labels and error messages.

Color contrast meeting WCAG AA where practical.

Charts accompanied by text or tables.

Mobile-responsive survey completion, even though no native mobile app is planned.

Plain-language methodology explanations suitable for high-school students.

Localization

Keep interface strings outside components from the beginning.

Allow Indonesian and English user-generated content.

Decide the initial UI language with pilot participants; do not let localization block the first vertical slice.

17. Analytics and success measurement

17.1 North-star outcome

Percentage of active pilot projects that complete the full evidence-to-impact loop with an approved research plan, predeclared primary metric, baseline, post measurement, and reviewed final report.

17.2 Product metrics

Metric

Definition

Pilot use

Report clarification completion

Submitted reports that answer at least one useful clarification

Tests whether framing help is usable

Duplicate usefulness

Suggested matches confirmed relevant by moderators

Tunes embedding threshold

Validation conversion

Published clusters that reach validated status

Detects whether reports become actionable

Research-plan approval cycle

Median review rounds before approval

Finds confusing requirements

Survey completion

Started versus submitted eligible responses

Finds friction

Baseline compliance

Approved projects with baseline recorded before action

Core quality indicator

Full-loop completion

Projects reaching reviewed final report

North-star input

Mentor attention time

Estimated review time per project per week

Checks administrative burden

AI acceptance/edit/dismissal

Outcome per AI feature

Identifies valuable versus noisy assistance

Safety routing accuracy

Moderator-confirmed sensitive flags and misses

Validates safeguards

17.3 Educational/research measures

Score comparable projects before and during the pilot using a human-reviewed rubric:

Problem specificity.

Evidence quality.

Research-question quality.

Sampling and ethics quality.

Presence and timing of baseline.

Quality of success metric.

Match between conclusion and evidence.

Transparency about limitations and failure.

Project completion.

Time from idea to validated proposal.

17.4 Pilot success criteria

The pilot is successful enough to continue if:

At least three teams complete the full loop.

At least 80% of approved projects define a primary metric and baseline before intervention.

Mentors report that the review workflow is manageable.

No critical privacy incident occurs.

Most pilot users can submit a problem and find its status without assistance.

Duplicate suggestions are useful often enough to reduce manual searching, even if not perfect.

At least one project produces a useful result, including an honest negative or inconclusive result.

These are planning targets and should be finalized after interviews with Pilar staff.

18. Pilot plan

18.1 Recommended pilot cohort

20–40 students.

3–5 student project teams.

2–4 teacher mentors.

1 OSIS reviewer.

1–2 school administrators/moderators.

18.2 Pilot boundaries

One school.

Selected grades or clubs rather than the entire student body.

A limited set of non-sensitive problem categories at launch.

School-only access.

Fixed pilot window with a beginning, review midpoint, and end.

Manual moderator oversight for all newly published problem reports during the first weeks.

18.3 Rollout stages

Stage A — Discovery and policy alignment

Interview students, mentors, OSIS, and the relevant project coordinator.

Map the school's present concern-reporting and project workflows.

Confirm safeguarding, survey, consent, and publication rules.

Choose two realistic pilot problem areas.

Stage B — Prototype test

Test clickable flows with 5–8 students and 1–2 mentors.

Observe whether terms such as evidence, baseline, intervention, and impact are understood.

Revise forms before backend complexity increases.

Stage C — Closed alpha

Use synthetic problems and survey responses.

Complete one end-to-end rehearsal with staff.

Test permission boundaries and private-report handling.

Stage D — Live pilot

Onboard the selected cohort.

Hold a short training session.

Run weekly mentor and moderation checks.

Capture usability issues and workflow delays.

Stage E — Evaluation

Compare project artifacts against the pre-pilot rubric.

Interview users.

Review privacy and moderation events.

Decide which V2 features solve observed problems rather than imagined ones.

19. Implementation roadmap

The sequence is intentionally vertical. Each milestone should produce something demonstrable and tested.

Milestone 0 — Discovery package

Deliverables:

Interview guide.

Current-workflow map.

Pilot policy decisions.

Vocabulary and role definitions.

Prioritized pilot use cases.

Exit criteria:

A school stakeholder confirms the workflow and reviewers.

Sensitive-report and survey rules have named owners.

Milestone 1 — Foundation

Deliverables:

Repository and environment configuration.

Authentication.

School-scoped roles and permissions.

React application shell.

FastAPI modules and database migrations.

Audit foundation.

CI for linting, type checks, tests, and migrations.

Exit criteria:

Each role can sign in and sees only permitted routes.

Permission tests pass at API level.

Milestone 2 — Voice vertical slice

Deliverables:

Problem form.

Private review queue.

Problem feed and cluster page.

Structured signals.

Evidence upload.

Manual cluster merge.

Status history and official update.

Then add:

Problem framing AI.

Embedding-based duplicate suggestions.

Exit criteria:

A report can be submitted, moderated, clustered, validated, and updated.

AI failure does not prevent submission.

Milestone 3 — Research vertical slice

Deliverables:

Research plan editor.

Versioned mentor review.

Initial methodology rules.

Evidence and claim links.

Limited survey builder and response flow.

Basic analysis.

Exit criteria:

A validated problem can become an approved study and collect test responses.

Anonymous export contains no identifying field.

Milestone 4 — Impact vertical slice

Deliverables:

Intervention proposal.

Theory of change.

Team, tasks, and milestones.

Metrics and baseline guard.

Observation entry.

Before/after display.

Impact report and mentor review.

Exit criteria:

One synthetic example completes the full loop.

Unsupported causal wording is flagged.

Milestone 5 — Governance and pilot readiness

Deliverables:

Mentor attention queue.

OSIS overview.

Admin configuration and audit viewer.

Notifications.

Accessibility pass.

Security review and backup/restore rehearsal.

Seed data and onboarding materials.

Exit criteria:

Role-based pilot rehearsal passes.

Critical security and privacy findings are resolved.

Milestone 6 — Pilot and evaluation

Deliverables:

Onboarding.

Support and incident process.

Weekly metrics review.

User interviews.

Pilot evaluation report.

Evidence-based V2 backlog.

20. Testing strategy

Unit tests

State-transition rules.

Permission policies.

Survey calculations.

Methodology rules.

Duplicate-signal constraints.

Impact-language guard.

Integration tests

Authentication and role boundaries.

Report submission to moderation.

Cluster merge and unmerge.

Survey version, publish, response, close, and export.

Review approval and changes requested.

Metric baseline and observations.

Audit-event creation.

End-to-end tests

Student submits a normal report; moderator publishes and clusters it.

Student submits a sensitive report; it never appears publicly.

Leader creates research, receives changes, revises, and gains approval.

Anonymous respondent completes a survey; researcher sees only authorized aggregate data.

Project cannot activate without primary metric and baseline plan.

Team completes impact report; mentor requests changes and later approves it.

AI provider fails; manual flow completes successfully.

Security tests

Horizontal authorization: one student cannot open another team's restricted draft.

Vertical authorization: students cannot call moderator endpoints.

File upload validation.

Rate limiting.

Survey replay/duplicate submission.

Stored and reflected XSS in user-generated content.

Export permission and anonymity leakage.

Audit logging without sensitive payloads.

Usability tests

Ask users to complete these without coaching:

Submit a measurable problem.

Understand whether a report is public or private.

Find the latest official response.

Turn a cluster into a research question.

Correct a leading survey question.

Explain what the baseline means.

Find what a mentor requested them to change.

21. Risks and mitigations

Risk

Likely effect

Mitigation

Product becomes a complaint wall

Conflict, low-quality submissions

Structured signals, moderation, neutral clusters, evidence requirements

Scope becomes too large

Project never reaches pilot

Enforce V1 boundary and milestone exit criteria

Students distrust anonymity

Low participation or unsafe disclosure

Plain-language privacy, minimal collection, verified anonymous exports

AI gives confident but poor advice

Bad research or loss of trust

Structured output, deterministic rules, explanations, human approval, feedback tracking

Duplicate matching merges unrelated concerns

Context is lost

Suggestions only, moderator decision, reversible merge

Mentors receive too much work

Slow approvals and abandonment

Exception-based queues, templates, small cohort, configurable requirements

Projects optimize for positive results

Hidden failures or weak claims

Require limitations, negative results, and predeclared metrics

Sensitive reports reach unauthorized users

Serious privacy harm

Private-by-default routing, strict permissions, access audit

Survey subgroups identify respondents

Privacy leakage

Suppress small groups and restrict exports

School does not act on validated issues

Loss of student trust

Official status, response owner, and update history; communicate limits honestly

Product is treated as emergency reporting

Delayed help

Prominent notice and direct school safeguarding route

22. Seed data for development

Use clearly labeled synthetic data only:

30 individual reports.

12 problem clusters.

8 research projects across all states.

6 surveys with 20–100 synthetic responses.

5 intervention projects.

3 completed impact reports, including one negative and one inconclusive result.

8 users across all roles.

Recommended example clusters:

Assessment deadline concentration.

Canteen queue congestion.

Competition and opportunity discoverability.

Club information fragmentation.

Waste sorting confusion.

Quiet study-space availability.

Synthetic records must display a development-data label and must never be presented as actual Pilar findings.

23. Open decisions for school discovery

These should be answered before production pilot configuration, but they do not block wireframing:

Which staff role owns private and sensitive reports?

What urgent-help instructions and contacts should appear?

Which grades and project groups join the first pilot?

Should new non-sensitive reports require moderation before publication during the full pilot?

Which survey types require teacher approval?

Can students publish impact pages outside the school?

How long should reports, responses, and uploaded files be retained?

Is English, Bahasa Indonesia, or bilingual UI preferred for the pilot?

Which existing account system, if any, should authentication use?

What counts as official OSIS versus school-administration communication?

Who can validate a problem cluster?

Which two real problem areas are appropriate for the first live test?

24. Definition of pilot-ready

ImpactOS V1 is pilot-ready only when all of the following are true:

The complete core loop works with one synthetic scenario.

All P0 requirements have passed acceptance testing.

Student, mentor, OSIS, moderator, and admin permissions have automated tests.

Sensitive reports cannot appear in public feeds without human approval.

Anonymous survey exports have been checked for identity leakage.

AI downtime does not block any required workflow.

Baseline and primary-metric rules are enforced.

Backups and restore have been tested.

The school has assigned moderation and safeguarding owners.

Pilot participants have onboarding instructions.

A process exists to report bugs, privacy concerns, and harmful content.

25. Recommended immediate next planning deliverables

Do not begin full implementation from this PRD alone. Complete these artifacts next, in order:

School discovery interview pack — separate question sets for students, mentors, OSIS, and administration.

Current-state versus future-state workflow map — show exactly what changes from the school's existing process.

Low-fidelity wireframes — student problem flow, research workspace, impact workspace, mentor queue, and moderation queue.

Clickable prototype test script — five tasks and interview questions for users.

Data dictionary and ERD v1 — exact fields, types, nullability, indexes, and retention classification.

Permission specification — endpoint-level and record-level rules.

API contract v1 — OpenAPI resource schemas, errors, pagination, and state transitions.

AI specification — versioned prompts, JSON schemas, methodology rules, fallback behavior, and evaluation set.

Engineering milestone backlog — small tickets mapped to this PRD's requirement IDs.

The correct next move is the school discovery interview pack and low-fidelity workflow/wireframe specification, because those can invalidate incorrect assumptions before expensive backend work begins.

26. Final product boundary

ImpactOS succeeds when it changes the structure of student action:

Not “I have an idea, so I should build it,” but “A real problem exists; here is the evidence; here is what we tried; and here is what honestly changed.”

PilarVoice, ResearchOS, and ImpactForge are therefore not separate products or decorative navigation tabs. They are the discovery, understanding, and action stages of a single accountable school-impact system.