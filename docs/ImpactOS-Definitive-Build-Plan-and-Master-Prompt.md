ImpactOS — Simplified Essence, Workflow, and Master Implementation Prompt

Pilot brand: Pilar Impact Lab
School: Sekolah Pilar Indonesia
Product stage: Build-ready closed alpha using synthetic data
Date: 23 August 2026

Part I — The simple essence

The product in one sentence

ImpactOS is a school web application that helps students identify a real problem, prove that it exists, research it responsibly, try a solution, and measure what changed.

What makes it different

Most school platforms stop at one of these stages:

collecting complaints;

conducting surveys;

managing projects; or

publishing final reports.

ImpactOS connects all four. Every project preserves a visible evidence trail:

problem → affected people → evidence → research → intervention → measurement → impact

The platform is therefore not three disconnected products. The earlier concepts become three parts of one journey:

Voice: What problem exists, and who experiences it?

Research: What does the evidence actually show?

Impact: What did we try, and what honestly changed?

The simplest example

A student reports that major Grade 10 assignments often share the same deadlines.

The system asks clarifying questions and suggests related reports.

A moderator groups similar reports into one problem page.

Other students indicate that they are affected or contribute evidence.

A team investigates the pattern through an approved research plan and survey.

The team proposes a shared assessment calendar.

Before starting, it records a baseline: the current number of deadline conflicts.

After the pilot, it records the same metric again.

The final report shows the observed change, evidence, limitations, and next action.

OSIS or the school publishes an official update.

The five essential workspaces

Problems — report, clarify, group, validate, and follow school problems.

Research — define questions, methods, surveys, evidence, and limitations.

Impact Projects — propose interventions, organize work, and define metrics.

Review — let mentors approve or request changes without reading everything.

Moderation and Response — protect sensitive reports and communicate what the school is doing.

What AI does

AI may:

make a vague report more specific;

suggest possible duplicate problems;

suggest research questions;

explain weak methodology or survey wording;

warn when conclusions exceed the evidence;

summarize why a project needs mentor attention.

AI may not:

decide whether an accusation is true;

punish or rank a student;

merge, publish, approve, or reject work by itself;

invent evidence or results;

make school policy;

claim that an intervention caused a result without an appropriate method.

The strict V1 boundary

Build only what is necessary to complete and protect the full loop.

V1 includes:

school-managed accounts and roles;

problem reporting and private moderation;

duplicate suggestions and moderator-controlled clusters;

structured student signals and evidence;

research plans and mentor review;

a small survey builder and basic analysis;

intervention proposals, tasks, milestones, and theory of change;

primary metric, baseline, post-measurement, and impact report;

official response history, notifications, and audit events.

V1 does not include:

public chat or social feeds;

likes, leaderboards, badges, or points;

a full LMS or Jira replacement;

custom-trained models;

advanced causal inference;

arbitrary spreadsheet analytics;

a mobile application;

multi-school administration;

automatic policy or disciplinary decisions.

Are we ready to build?

Yes, for a local or hosted closed alpha using synthetic data.

The PRD, workflow map, wireframes, prototype test script, and discovery pack provide enough product definition to implement the core system.

No, not yet for live student data. Before live deployment, Pilar must confirm:

who owns sensitive/private reports and the urgent-help route;

who may validate problems, approve surveys, and publish official responses;

authentication, retention, consent, and external-publication policies;

the pilot cohort, categories, and preferred UI language.

Development and school discovery can proceed in parallel. Until those decisions are confirmed, the product must remain in DEMO or CLOSED_ALPHA mode with synthetic data.

Part II — Definitive implementation plan

1. Readiness decision

The project has enough definition to begin implementation now, but development and deployment must be treated as separate readiness levels.

Level

Meaning

Current readiness

Local prototype

Interfaces and workflows use temporary or synthetic data

Ready

Closed alpha

Full database-backed workflow with synthetic demo users and restricted testers

Ready to build

School pilot

Selected real users and limited categories

Blocked by school policy confirmations and user testing

Production

Broader school use with operational ownership, retention, incident handling, and support

Not yet in scope

The immediate target is a database-backed closed alpha, not a visual mockup and not a production rollout.

2. Delivery strategy

Build a single complete vertical slice through the product before adding secondary polish. The critical path is:

Foundation
   ↓
Problem intake and moderation
   ↓
Problem cluster and validation
   ↓
Research plan and mentor review
   ↓
Survey and evidence collection
   ↓
Intervention and baseline gate
   ↓
Impact measurement and report
   ↓
Role dashboards, security, and pilot hardening

Do not build all dashboards first. Do not build AI before the manual workflow exists. Do not begin advanced analysis before survey privacy and versioning work.

Recommended implementation rhythm

Use short milestones with an explicit exit gate.

Keep the frontend and backend integrated within each milestone.

Add permissions and audit behavior at the same time as each feature, not afterward.

Demonstrate each milestone using the same synthetic golden-path scenario.

Record test results and unresolved decisions after every milestone.

Do not start the next milestone while a critical exit criterion is failing.

Realistic effort

For one student developer working part-time with a coding agent, a credible closed alpha is roughly 10–14 focused weeks. A small two-to-three-person team may complete it in 6–9 weeks. These are planning ranges, not promises; school workload and debugging can change them.

3. Product layers and dependencies

Layer A — Platform foundation

Provides:

configuration;

authentication;

school membership;

roles and record-level permissions;

application shell;

database migrations;

files;

notifications;

audit primitives;

demo-mode seed data.

Every later layer depends on this.

Layer B — Voice

Provides:

problem reports;

visibility and sensitivity routing;

moderator review;

problem clusters;

student signals;

evidence;

official status history.

Research cannot start until a permitted problem cluster exists.

Layer C — Research

Provides:

research plans and versions;

methodology rules;

mentor review;

surveys and approved versions;

responses and analysis;

claims and evidence mapping.

An impact project should normally depend on approved or completed research.

Layer D — Impact

Provides:

intervention proposal;

theory of change;

team, tasks, and milestones;

primary and secondary metrics;

baseline gate;

observations;

impact report and review.

Layer E — Governance and operations

Provides:

mentor attention queue;

OSIS overview;

admin configuration;

restricted moderation queue;

audit viewer;

system health;

pilot controls.

4. End-to-end workflow contract

Every stage needs a clear input, output, responsible actor, and blocking rule.

Stage

Input

Primary action

Output

Responsible actor

Blocking condition

Discover

Student observation

Submit structured report

Submitted report

Student

Missing required description/scope/visibility

Route

Submitted report

Review sensitivity and visibility

Private route or moderated public candidate

Moderator

Sensitive flag requires human review

Group

Moderated report

Compare and merge when appropriate

Report linked to cluster

Moderator

No silent automatic merge

Validate

Cluster, signals, evidence

Decide whether evidence is sufficient

Validation decision

Authorized reviewer

Decision requires reason

Plan research

Validated cluster

Create plan

Versioned research draft

Student leader

Required plan sections missing

Review research

Submitted plan

Approve or request changes

Review decision

Mentor

Data collection blocked until approval

Collect

Approved plan/survey

Receive evidence and responses

Closed evidence snapshot

Research team

Survey must be open and approved

Analyze

Closed or active dataset

Produce descriptive findings

Findings and limitations

Research team

Privacy/invalid-statistic rules

Propose

Findings and evidence

Create intervention

Versioned proposal

Student leader

Required theory, risks, metric plan missing

Approve action

Proposal

Review intervention

Approved project

Mentor/reviewer

Baseline plan and primary metric required

Activate

Approved project

Record baseline and begin

Active project

Project leader + reviewer rules

Baseline observation missing unless documented exception

Measure

Active/completed action

Record post/follow-up data

Metric observations

Project team

Units and collection method must remain compatible

Report

Evidence and observations

Draft final report

Versioned report

Project leader

Results/limitations sections missing

Review impact

Submitted report

Approve/request changes

Review decision

Mentor/reviewer

Unsupported claims must be corrected/acknowledged

Publish/respond

Approved report

Publish allowed summary/update

Internal impact page and response history

Authorized OSIS/admin

Publication permission and visibility

5. Detailed actor workflows

5.1 Student problem workflow

Student signs in and opens Report a Problem.

The form begins with observable facts rather than a proposed solution.

Student enters title and description.

Student selects affected group, scope, category, frequency, severity, and visibility.

Student may add a file or structured observation.

The system runs local validation immediately.

AI optionally returns a structured interpretation and no more than three clarifying questions.

Student accepts, edits, or dismisses each suggestion.

The system displays possible related clusters without forcing a choice.

Student confirms the final content and privacy setting.

Backend records the submission and runs sensitivity routing.

A normal report goes to configured moderation; a potentially sensitive report goes only to restricted review.

Student sees a receipt stating its exact status, visibility, and next step.

Later, the student receives notifications about moderation, merging, status changes, or official responses.

Failure and recovery:

AI timeout: continue manually.

Upload failure: preserve form draft and allow retry/removal.

Duplicate suggestion rejected: submit as a new report; moderator decides later.

Sensitive content detected: do not show a public preview or public URL.

5.2 Moderator workflow

Moderator opens the restricted queue.

Queue separates private/sensitive reports from ordinary visibility and duplicate decisions.

Moderator opens a report through an audited restricted-access action.

Moderator reviews the author's visibility choice, sensitivity reason, and school-configured help route.

Moderator routes, publishes, keeps private, requests clarification, or archives according to configured authority.

For duplicates, moderator opens the original report and candidate cluster side by side.

Moderator chooses merge or not-a-match and provides a reason.

Merge retains the original report, author, attachments, permissions, and audit history.

Unmerge is available to an authorized moderator with a reason.

The author receives only the information their visibility and safety policy permits.

5.3 Problem validation workflow

Published cluster collects structured signals and permitted evidence.

Each student can use each signal type once and may retract it.

Evidence records source, type, observation date, relevance, visibility, and file metadata.

The system summarizes reach, frequency, severity, evidence strength, trend, and actionability separately.

AI or rules may recommend priority, but never set it as school policy.

Authorized reviewer marks the cluster validated or leaves it gathering evidence.

The decision includes rationale and next action.

Cluster timeline records the transition and notifies followers.

5.4 Research and mentor-review workflow

Authorized student leader selects Investigate This Problem.

System creates a research draft linked to the cluster.

Leader completes question, hypothesis, population, variables, operational definitions, method, sampling, collection, ethics, limitations, and conclusion boundary.

AI may suggest descriptive, comparative, or associational questions.

Deterministic rules create warnings with explanations and corrections.

Team links existing evidence and records claims.

Required-field completeness is separate from warning severity.

Leader submits a frozen plan version for mentor review.

Mentor reviews the submitted snapshot, not a moving draft.

Mentor approves, requests changes, or comments.

If changes are requested, the team creates a new draft based on the reviewed version.

Review history preserves version, actor, time, comments, and decision.

Approved research may begin collection.

5.5 Survey workflow

Team creates a survey inside approved research.

Team configures audience, purpose, privacy, one-response policy, dates, and consent/introduction copy.

Team adds only V1 question types: multiple choice, Likert, number, and short text.

Rules and AI review wording and privacy risks.

Critical issues block submission/publishing; other warnings require resolution or acknowledgement.

Team submits an immutable version for review.

Mentor/admin approves or requests changes.

Approved survey publishes to a unique code.

Respondent sees purpose, eligibility, privacy, and consent before questions.

Backend checks eligibility and survey state.

Submission uses idempotency protection.

Anonymous identity enforcement remains separated from researcher-visible response data.

Survey closes manually or at the configured time.

Analysis shows only valid summaries for each type.

Authorized CSV export applies privacy serialization and records an audit event.

5.6 Intervention workflow

Leader selects Create an Intervention from approved/completed research.

System carries links to the problem, research, and selected evidence.

Team defines target users, proposed intervention, rationale, theory of change, risks, resources, timeline, team, and mentor.

Team defines exactly one primary metric and up to three secondary metrics.

Every metric includes unit, direction, collection method, target, and baseline plan.

Team submits a frozen proposal version.

Mentor/reviewer approves or requests changes.

Approved project remains unable to activate until the baseline observation exists.

An authorized reviewer may record an exceptional activation with a visible reason; ordinary users cannot bypass the gate.

Active project uses lightweight tasks, milestones, and updates.

5.7 Measurement and impact workflow

Team records metric observations as baseline, during, post, or follow-up.

Every observation records date, value, sample size when relevant, recorder, notes, and evidence.

System checks metric unit and method compatibility.

Results page calculates valid absolute/percentage changes.

Language guard uses “observed change” by default.

Team generates a report containing implementation, results, limitations, failures, and next steps.

Negative or inconclusive outcomes remain valid completion states.

Team submits a frozen report version.

Mentor/reviewer approves or requests changes.

Authorized publisher releases only the allowed internal summary and official update.

5.8 Mentor attention workflow

System generates deterministic attention reasons rather than a mysterious risk score.

Reasons include privacy warning, review requested, changes resubmitted, missing metric, missing baseline, due soon, and stale activity.

Mentor filters or sorts the queue.

Mentor opens an artifact snapshot with relevant history.

Mentor makes a decision or leaves a comment.

The queue updates based on the decision and state transition.

The team receives a notification with the exact next action.

6. Data architecture plan

6.1 Migration sequence

Create migrations in dependency order:

Schools, users, memberships, roles, assignments, invitations.

Grades, classes, categories, school settings.

Files and audit logs.

Problem reports, clusters, memberships, signals, status history, official updates.

Evidence items.

Research projects, plan versions, variables, claims, evidence links.

Surveys, versions, questions, responses, answers.

Impact projects, members, tasks, milestones.

Metrics, observations, project updates, report versions.

Reviews, review comments, notifications, moderation flags, AI runs.

pgvector extension and embedding indexes when the database supports them.

Each migration needs downgrade behavior tested in development. The application must boot against a database built from zero migrations.

6.2 Transaction boundaries

Use a single transaction for:

report submission plus initial status history;

merge/unmerge plus audit event;

review decision plus state transition plus notification outbox entry;

survey version publish;

response and answers insertion;

project activation plus baseline validation;

official update publication.

Send external notifications or AI jobs after commit through an outbox/background job rather than inside the database transaction.

6.3 Query/index plan

Index:

every foreign key used in feeds;

school_id + status + updated_at for core lists;

school_id + category_id + status for problem discovery;

assigned mentor + state for review queues;

survey code and state;

project member and assignee relationships;

audit timestamp, actor, entity, and action;

pgvector cluster embedding using an index appropriate to pilot data volume.

Avoid premature denormalized counters unless profiling shows a need. Correctness is more important at pilot scale.

7. Backend engineering plan

Service layers

Routes parse input and return schemas.

Permission policies decide whether the actor may perform the action on the record.

Domain services enforce state transitions and invariants.

Repositories/data access isolate query details.

Event/outbox services create notifications and background jobs.

AI adapters remain behind interfaces and never mutate canonical entities directly.

Shared backend capabilities

request ID middleware;

authenticated actor context;

school scope enforcement;

standard error envelope;

cursor pagination;

optimistic version conflict handling;

audit helper with safe metadata allowlist;

idempotency service for survey responses and high-value mutations;

file storage abstraction;

health and readiness endpoints;

feature flags/application mode.

API completion rule

An endpoint is not complete until it has:

request and response schemas;

authentication/authorization;

domain validation;

expected errors;

transaction handling;

audit/notification behavior where relevant;

unit or integration tests;

frontend integration or explicit internal-only status;

8. Frontend engineering plan

Shared frontend foundation

route tree with role guards;

typed API client;

query-key conventions;

mutation error handling;

accessible component primitives;

form field and validation components;

status badge system;

permission-aware action component;

confirmation and reason-dialog patterns;

loading, empty, error, offline/AI-unavailable, and forbidden states;

responsive application shell;

demo-data banner.

Feature construction order

Within each feature:

Define TypeScript types and Zod schemas.

Create API client functions and query keys.

Build read-only list/detail states.

Build create/edit forms.

Add transitions and decisions.

Add optimistic updates only when rollback is safe.

Add accessibility and responsive behavior.

Add component/integration tests.

Verify with the seeded golden path.

UI state requirements

Every important screen must handle:

initial loading;

empty results;

partial content;

validation errors;

permission denied;

version conflict;

backend unavailable;

AI unavailable;

success confirmation;

destructive/reversible decision confirmation.

9. AI/NLP implementation plan

Phase 1 — Interfaces and deterministic fallback

Define schemas for every AI capability.

Implement provider interface and disabled/fake adapter.

Build UI cards and manual fallback.

Record outcome telemetry.

Phase 2 — Problem framing

Problem extraction.

Clarification questions.

Sensitivity first-pass flag.

Structured validation and one retry.

Phase 3 — Duplicate suggestions

Background embedding generation.

Vector query limited by school/category.

Metadata compatibility.

Moderator feedback capture.

Phase 4 — Research/survey assistance

Question suggestions.

Rule-based methodology checks.

AI explanations for rule results.

Survey wording critique.

Phase 5 — Impact language

Identify unsupported causal wording.

Suggest observational rewrite.

Never edit the saved report silently.

Evaluation dataset

Create synthetic fixtures with expected outcomes:

at least 30 problem reports including duplicate and non-duplicate pairs;

normal and sensitive examples without real personal data;

research questions across descriptive/comparative/associational types;

leading, neutral, ambiguous, and double-barrelled survey questions;

supported and unsupported impact claims.

Record precision/recall or reviewer agreement where meaningful, but do not invent production-quality metrics from synthetic data.

10. Security and privacy work plan

Threats to test explicitly

student reads another student's restricted draft by changing an ID;

student calls a moderator endpoint directly;

OSIS sees a sensitive cluster/report count or snippet;

mentor reads unassigned private work;

anonymous export includes identity or reversible token;

private file URL remains usable by an unauthorized account;

malicious rich text or filename produces XSS;

survey response is replayed;

user changes a frozen approved version;

logs contain sensitive text;

cross-school access is possible through a missing school_id condition.

Security review gates

Gate 1: permission matrix tests before Voice completion.

Gate 2: restricted-report leakage tests before Research begins.

Gate 3: anonymous-response/export review before survey alpha.

Gate 4: full role and file-access review before closed-alpha release.

11. Testing and quality plan

Test pyramid

Many domain/unit tests for transitions, rules, permissions, and calculations.

Integration tests for transactions, queries, versioning, and privacy.

Component tests for forms and decision UI.

A small set of full golden-path Playwright tests.

Required fixtures

five role accounts plus admin;

a normal report;

a private report;

duplicate and non-duplicate cluster candidates;

research plan with changes requested;

approved survey and anonymous responses;

project missing a baseline;

project with baseline/post observations;

negative and inconclusive report.

Release verification command set

Document one command or task runner target for:

starting local infrastructure;

applying migrations;

loading demo data;

backend lint/type check/test;

frontend lint/type check/test/build;

Playwright tests;

starting both applications;

resetting demo data safely.

12. Milestone plan and exit gates

Milestone 0 — Repository audit and decision register

Objective: understand what exists and freeze initial assumptions.

Tasks:

inspect repository and working tree;

record existing architecture and commands;

list reusable code and gaps;

create docs/DECISIONS.md;

create docs/LIVE_DEPLOYMENT_BLOCKERS.md;

confirm golden-path seed scenario;

write milestone checklist.

Exit gate:

repository runs or a new scaffold is demonstrably healthy;

no user work was overwritten;

unresolved policy decisions are explicit.

Milestone 1 — Foundation

Objective: secure skeleton with real persistence.

Tasks:

frontend/backend scaffolding;

PostgreSQL and migrations;

schools/users/memberships/roles;

invitations/login/logout/session;

permission framework;

demo mode and seed accounts;

application shell and role routing;

audit/notification primitives;

CI and base tests.

Demonstration:

switch between demo roles;

prove a student cannot access an admin route or endpoint;

deactivate an account without losing attribution.

Exit gate:

empty-database migration passes;

role permission tests pass;

frontend production build passes;

no public registration exists.

Milestone 2 — Voice

Objective: complete problem intake-to-cluster workflow.

Tasks:

problem draft/wizard;

visibility choices;

sensitivity routing;

moderation queue;

cluster create/merge/unmerge;

problem index/detail;

four signals;

evidence metadata and files;

status history and official update;

AI framing and duplicate suggestion after manual path works.

Demonstration:

normal report becomes a published cluster;

sensitive report remains completely restricted;

duplicate merge is reversible;

follower sees an official status update.

Exit gate:

private-report leakage test suite passes;

no automatic merge or publication occurs;

AI-disabled manual flow passes end to end.

Milestone 3 — Research

Objective: complete approved research and survey workflow.

Tasks:

research creation from cluster;

plan editor and versions;

variables and claims/evidence;

methodology rules;

mentor review;

survey builder/preview;

survey version approval;

respondent experience;

results and privacy-safe export.

Demonstration:

mentor requests changes on version 1;

leader revises and gains approval on version 2;

anonymous respondent submits;

researcher sees allowed analysis but no identity.

Exit gate:

approved versions are immutable;

invalid statistics are not shown;

anonymous export privacy tests pass;

survey replay/idempotency test passes.

Milestone 4 — Impact

Objective: complete intervention-to-impact workflow.

Tasks:

project creation from research;

proposal and theory of change;

team, tasks, milestones, updates;

metrics and baseline plan;

baseline activation gate;

observations and comparisons;

report generation/versioning;

impact review.

Demonstration:

project activation fails without a baseline;

baseline permits activation;

post observation produces an observed-change result;

negative/inconclusive report completes review.

Exit gate:

metric invariants pass;

causal-language warning passes fixtures;

complete golden path reaches approved impact report.

Milestone 5 — Role workspaces and operations

Objective: make the system usable by every role.

Tasks:

role-aware dashboards;

mentor attention queue;

OSIS overview and official updates;

admin configuration;

audit viewer;

notifications center;

search/filter/pagination;

system health and AI status.

Exit gate:

every role completes its assigned prototype task;

attention reasons are explainable;

OSIS cannot access restricted data.

Milestone 6 — Closed-alpha hardening

Objective: make the synthetic-data alpha stable and testable.

Tasks:

complete accessibility pass;

responsive/mobile survey pass;

performance profiling;

security review;

file-access review;

backup/restore rehearsal;

production-like staging configuration;

user and developer documentation;

full end-to-end test run.

Exit gate:

definition of done passes;

no critical/high security issue remains;

all live-deployment blockers remain visibly unresolved rather than silently defaulted.

Milestone 7 — School discovery and live-pilot preparation

This milestone is organizational as well as technical.

Tasks:

run the prepared interviews;

test wireframes/closed alpha with representative users;

synthesize findings;

resolve safeguarding and authority decisions;

choose cohort and categories;

finalize authentication and retention;

update PRD, permissions, UI language, and configuration;

conduct staff rehearsal with synthetic data;

complete go/no-go review.

Exit gate:

named owners exist for moderation, safeguarding, support, and publication;

privacy/consent/retention decisions are documented;

school sponsor signs off on limited live pilot;

pilot incident and rollback process exists.

13. Suggested sprint sequence

Sprint

Main goal

Demonstrable result

0

Audit and scaffold

Repository runs; decisions/blockers documented

1

Auth, school scope, roles

Demo users sign in with enforced permissions

2

Problem drafts and submission

Student completes normal/private report flow

3

Moderation, clusters, signals

Moderator safely publishes/merges; student validates

4

Evidence, status, duplicate engine

Evidence trail and duplicate suggestions work

5

Research plan and rules

Student creates plan and understands warnings

6

Mentor review and versions

Changes-requested/approved workflow works

7

Survey builder and approval

Approved immutable survey opens

8

Responses, analysis, export

Anonymous collection and safe summaries work

9

Intervention and project workspace

Approved proposal with tasks/milestones works

10

Metrics, baseline, observations

Activation gate and before/after comparison work

11

Report and official response

Reviewed impact report reaches internal publication

12

Dashboards and notifications

Every role sees its next actions

13

Security, accessibility, E2E

Closed-alpha release candidate passes gates

If a sprint takes longer, preserve the order rather than cutting the security or privacy work.

14. Initial engineering backlog

Epic FND — Foundation

FND-001 repository audit.

FND-002 environment/config system.

FND-003 PostgreSQL and migrations.

FND-004 school/user/membership schema.

FND-005 invite-only authentication.

FND-006 RBAC and record policies.

FND-007 application shell.

FND-008 demo seed system.

FND-009 audit and notification primitives.

FND-010 CI and developer commands.

Epic VOI — Voice

VOI-001 problem wizard.

VOI-002 report draft API.

VOI-003 submission and sensitivity route.

VOI-004 moderation decision.

VOI-005 cluster model/detail.

VOI-006 merge/unmerge.

VOI-007 structured signals.

VOI-008 evidence upload/metadata.

VOI-009 status history.

VOI-010 official updates.

VOI-011 framing AI.

VOI-012 embeddings and duplicate candidates.

Epic RES — Research

RES-001 research creation.

RES-002 plan editor.

RES-003 immutable plan versions.

RES-004 variables.

RES-005 methodology rules.

RES-006 claims/evidence links.

RES-007 mentor review.

RES-008 survey builder.

RES-009 survey review and versions.

RES-010 respondent flow.

RES-011 analysis.

RES-012 safe export.

Epic IMP — Impact

IMP-001 create project from research.

IMP-002 proposal editor.

IMP-003 theory of change.

IMP-004 team management.

IMP-005 tasks/milestones.

IMP-006 metrics.

IMP-007 baseline plan and observation.

IMP-008 activation gate.

IMP-009 observations/comparison.

IMP-010 report generation and versions.

IMP-011 impact review.

Epic GOV — Governance

GOV-001 mentor attention queue.

GOV-002 OSIS overview.

GOV-003 admin configuration.

GOV-004 notification center.

GOV-005 audit viewer.

GOV-006 system/AI health.

GOV-007 accessibility hardening.

GOV-008 security review.

15. Project management workflow

For every ticket:

Link the requirement or workflow it implements.

Write acceptance criteria before coding.

Identify permission and privacy implications.

Identify database migration impact.

Implement backend/domain behavior.

Implement UI states.

Add tests.

Run targeted checks.

Verify the seeded scenario.

Update documentation and mark the ticket complete only with evidence.

Use ticket states:

BACKLOG → READY → IN_PROGRESS → REVIEW → VERIFIED → DONE

DONE means merged into the working branch, tests pass, and the acceptance criteria were manually or automatically verified.

16. Live-pilot blockers

The closed alpha must include a visible checklist for these unresolved decisions:

designated private-report owner;

urgent-help/safeguarding route;

problem-validation authority;

survey approval authority;

OSIS versus administration publication authority;

authentication provider;

pilot grades/groups;

launch categories;

consent wording;

retention period by record type;

external publication rule;

UI language;

incident-response owner;

support contact;

backup/restore expectation.

The application may implement configuration fields for these decisions, but must not fabricate Pilar's answers.

17. Final planning rule

The first successful release is not the one with the most features. It is the one in which a synthetic problem can safely and honestly become a reviewed impact report, while every role understands what it owns and private information stays private.

Part III — Master implementation prompt

Copy everything below into the coding agent working inside the project repository.

PROMPT START

You are the lead full-stack engineer and product implementation agent for ImpactOS, piloted at Sekolah Pilar Indonesia under the name Pilar Impact Lab.

Your job is to build a secure, responsive, testable closed-alpha web application that completes one connected workflow:

report a problem → validate it → research it → propose an intervention → record a baseline → run the intervention → measure the result → review and publish impact

Do not turn the product into a generic dashboard, social network, project-management clone, or all-purpose AI chatbot. Every feature must either complete this loop or protect it.

1. Working rules

Inspect the repository before changing anything. Read its README, package files, environment examples, migrations, tests, and existing architecture.

Preserve working code and existing user changes. Extend the current structure when it is sound.

If the repository is empty, create the monorepo described below.

Build in milestones, but continue through the complete closed-alpha vertical slice unless a genuine blocker exists.

Do not claim a feature is complete if its buttons, backend behavior, permissions, or tests are missing.

Do not use mock browser-only state for persistent core features. Store them through the backend and database.

Do not deploy, push, purchase services, or use real student data unless explicitly authorized.

Use synthetic seed data and visibly label the application DEMO DATA while policy decisions remain unresolved.

Keep AI provider failures non-blocking. Every required workflow must work manually.

Prefer simple, maintainable code over premature abstractions.

Run formatting, linting, type checking, backend tests, frontend tests, migrations, and production builds before finishing.

Document every important assumption and unresolved school-policy decision.

2. Product definition

ImpactOS helps students:

report observable school or community problems;

see whether related reports already exist;

contribute structured signals and evidence;

create a research plan linked to the problem;

collect approved survey data;

propose and run an intervention;

define success before acting;

compare baseline and post-intervention observations;

publish an honest report, including negative or inconclusive results.

The three conceptual stages are:

Voice: discovery and validation;

Research: investigation and evidence;

Impact: intervention and measurement.

These stages share data and navigation. Do not make them disconnected microsites.

3. Primary roles

Implement school-scoped role-based access control for:

Student contributor

Create, edit, and submit their own problem drafts.

Choose school-visible under their name, school-visible anonymously, or private review.

View allowed problem clusters.

Add structured signals.

Add permitted evidence.

Follow updates.

Participate in a research or project team when invited.

Student project leader

All student abilities plus:

Create and edit linked research plans.

Build surveys.

Link claims and evidence.

Create an intervention proposal.

Manage project members, tasks, milestones, metrics, observations, and reports.

Submit work for mentor review.

Mentor

View only assigned or otherwise permitted work.

Review research plans, surveys, interventions, and impact reports.

Approve, request changes, or comment.

View explainable attention warnings such as privacy risk, missing baseline, due soon, or stale work.

OSIS reviewer

View non-sensitive aggregate school problems.

View validated clusters and permitted project summaries.

Record priority rationale.

Link an OSIS initiative when permitted.

Publish official OSIS updates when authorized.

Administrator/moderator

Configure school structure, categories, roles, and pilot settings.

Review sensitive and private reports.

Decide visibility.

Merge and unmerge reports into clusters.

Assign mentors/reviewers.

Publish official school updates.

View audit history.

Deactivate accounts without destroying historical attribution.

Enforce permissions in backend services and endpoints. Hiding UI controls is not authorization.

4. Technical stack

Use this stack unless the existing repository already has an equivalent, working choice:

Frontend

Vite

React

TypeScript in strict mode

React Router

TanStack Query for server state

React Hook Form

Zod

Tailwind CSS

Recharts for accessible charts

Zustand only for small cross-step client state when URL or server state is unsuitable

Vitest and React Testing Library

Playwright for essential end-to-end flows

Backend

Python

FastAPI

Pydantic

SQLAlchemy 2 style

Alembic

PostgreSQL

pgvector

pytest

Redis and ARQ only when asynchronous jobs become necessary

Data/AI

NumPy and pandas for tested survey summaries

A configurable pretrained sentence-transformer for embeddings

A provider-neutral LLM adapter with structured JSON outputs

Deterministic methodology and safety rules outside the LLM

Local infrastructure

Docker Compose for PostgreSQL and optional Redis/object storage

.env.example with safe placeholders

S3-compatible file abstraction; local development adapter is acceptable

Separate development, test, closed_alpha, and production configuration

Recommended monorepo structure if starting from zero:

impactos/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── dashboard/
│   │   │   ├── problems/
│   │   │   ├── evidence/
│   │   │   ├── research/
│   │   │   ├── surveys/
│   │   │   ├── projects/
│   │   │   ├── impact/
│   │   │   ├── reviews/
│   │   │   ├── moderation/
│   │   │   ├── osis/
│   │   │   └── admin/
│   │   ├── hooks/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── styles/
│   │   ├── types/
│   │   └── utils/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── auth/
│   │   ├── schools/
│   │   ├── users/
│   │   ├── problems/
│   │   ├── clustering/
│   │   ├── evidence/
│   │   ├── research/
│   │   ├── methodology/
│   │   ├── surveys/
│   │   ├── analysis/
│   │   ├── projects/
│   │   ├── impact/
│   │   ├── reviews/
│   │   ├── governance/
│   │   ├── notifications/
│   │   ├── files/
│   │   ├── audit/
│   │   └── ai/
│   ├── alembic/
│   └── tests/
├── docs/
├── scripts/
├── docker-compose.yml
├── .env.example
└── README.md

5. Environment and live-data gate

Create an application mode setting:

APP_MODE=DEMO | CLOSED_ALPHA | PRODUCTION

In DEMO:

use synthetic seed data;

display a persistent DEMO DATA badge;

use a placeholder school safeguarding notice;

disable external publication;

allow demo user switching only in development.

In CLOSED_ALPHA or PRODUCTION, validate required configuration at startup:

designated safeguarding/help text or URL;

private-report owner role;

authentication configuration;

allowed pilot categories;

file limits;

retention-policy reference;

publication policy;

configured school name and UI language.

Do not silently use demo policy values with real data.

6. Visual and interaction direction

Build a calm, modern, credible school product. It should feel thoughtful and substantial, but not corporate, childish, or crowded.

Design language

Primary: deep navy/teal.

Background: soft neutral gray.

Surfaces: white with restrained borders and shadows.

Accent: muted teal or blue-green.

Warning: amber.

Danger/private: muted red.

Success: green.

Use consistent 8px spacing increments.

Use readable type at a minimum practical body size of 14–16px.

Use sentence case rather than excessive uppercase.

Use color plus icon/text; never color alone for status.

Avoid decorative gradients, glassmorphism, excessive rounded cards, and empty analytics cards.

Application shell

Desktop:

persistent left sidebar;

top bar with school/product identity, search, notifications, active role, and profile;

centered content with a readable maximum width;

contextual page actions in the header.

Mobile/tablet:

collapsible navigation drawer;

single-column forms;

sticky bottom action only when it improves a multi-step task;

survey response pages optimized for phones.

Primary navigation:

Dashboard

Problems

Research

Impact Projects

My Tasks

Review, OSIS, or Admin workspace when authorized

UX rules

Always show the current workflow status and the next valid action.

Explain why an action is blocked and how to fix it.

Mark AI content as Suggestion or Warning and provide Use, Edit, or Dismiss controls.

Mark private records with a lock label and plain-language visibility explanation.

Every review decision previews the next state.

Use progressive disclosure so students are not shown the entire research methodology form at once.

Preserve drafts automatically or clearly expose a save state.

Include empty, loading, error, permission-denied, and AI-unavailable states.

7. Required routes and screens

Implement these routes with guards and real backend integration.

Public or limited-access routes

/login
/invite/:token
/s/:publicCode
/help

The survey link may still require school authentication depending on its configuration.

Authenticated shared routes

/
/dashboard
/problems
/problems/new
/problems/reports/:reportId
/problems/:clusterId
/research
/research/new?problem=:clusterId
/research/:researchId
/research/:researchId/survey
/research/:researchId/analysis
/projects
/projects/new?research=:researchId
/projects/:projectId
/projects/:projectId/impact
/tasks
/notifications
/settings

Role workspaces

/mentor
/mentor/reviews/:reviewId
/osis
/moderation
/admin
/admin/users
/admin/configuration
/admin/audit

8. Screen specifications

8.1 Login and invitation

Pilar Impact Lab identity and concise product statement.

School-managed login or invitation acceptance.

No public self-registration.

Clear demo-account selector only in development/demo mode.

Error and expired-invitation states.

8.2 Role-aware dashboard

Student dashboard:

continue drafts or requested changes;

active research and projects;

assigned tasks;

followed problems and latest updates;

one contextual next-action card.

Mentor dashboard:

needs review;

privacy or methodology warnings;

missing metrics/baselines;

due soon;

stale projects;

recent review history.

OSIS dashboard:

emerging allowed problem categories;

validated but unactioned clusters;

active linked initiatives;

official updates due;

aggregate non-identifying trends.

Admin dashboard:

private review count;

duplicate decisions pending;

unresolved configuration;

user/role summary;

recent audit events;

background job and AI failure status.

8.3 Problems index

Search by title and summary.

Filters: category, status, scope, affected group, and updated date.

Sort: recently updated, strongest evidence, most affected, and school priority.

Cards show neutral title, concise summary, status, category, affected count, evidence count, and latest official update.

Do not show likes or a single popularity score.

Primary action: Report a Problem.

8.4 Report-a-problem wizard

Use four steps:

Describe — title and what is happening.

Scope — affected group, school scope, category, frequency, severity, and visibility.

Support — evidence upload or structured observation.

Review — AI interpretation, up to three clarification questions, duplicate candidates, privacy explanation, and final confirmation.

Visibility options:

school-visible under the author's name;

school-visible anonymously to students, with identity restricted to designated staff;

private review only.

Show the statement that ImpactOS is not an emergency channel and the configured urgent-help route.

On submission:

run sensitivity rules;

route sensitive reports to PRIVATE_REVIEW;

otherwise send to moderation according to configured policy;

enqueue embedding creation;

show a confirmation with the report state and what happens next.

8.5 Problem cluster page

Header:

neutral cluster title and summary;

category and scope;

status and latest update;

affected count and evidence count;

structured signal buttons.

Structured signals:

This affects me.

I have evidence.

I want to investigate.

I want to help solve it.

Tabs:

Overview

Related reports

Evidence

Research

Projects

Updates

Impact

Only show reports and evidence permitted for the current user. Never leak private source reports through counts, snippets, URLs, or exports.

8.6 Research workspace

Persistent header:

linked problem;

status;

assigned mentor;

required-section completion;

active warnings;

save and submit actions.

Sections:

research question and question type;

hypothesis;

population;

variables and operational definitions;

methodology;

sampling;

data collection;

ethics/privacy;

limitations;

conclusion boundary;

evidence and claims;

survey;

findings;

review history.

AI may suggest descriptive, comparative, or associational questions. Explain each label in student-friendly language.

Block mentor submission only for clearly missing required sections. Warnings should be correctable, not punitive.

8.7 Survey builder

V1 question types only:

multiple choice;

Likert scale;

number;

short text.

Capabilities:

add, edit, delete, duplicate, reorder, and mark required;

preview the respondent experience;

configure title, purpose, audience, anonymity, authentication, one-response policy, introduction/consent text, open date, and close date;

run deterministic and optional AI review;

submit for mentor/admin review;

publish an immutable approved version;

create a new version if an approved survey is edited.

Review warnings:

leading or loaded wording;

double-barrelled question;

ambiguity;

missing answer option;

sensitive or identifiable information;

population/audience mismatch.

Critical privacy warnings block publication until reviewed. Non-critical warnings may be acknowledged with a reason.

8.8 Survey response experience

Mobile-first layout.

Show research purpose, approximate length, eligibility, anonymity or identification terms, data visibility, and consent text.

Validate eligibility server-side.

Enforce one response according to policy.

Use an idempotency key to prevent accidental duplicates.

Show completion confirmation without repeating sensitive answers.

For anonymous surveys, never expose account ID, name, email, or a reversible respondent token to the research team.

8.9 Survey analysis

For authorized users, show:

valid response count;

missing count per question;

counts and percentages for categorical responses;

mean and median only where appropriate;

distribution charts;

written interpretation cautions;

CSV export when authorized.

Do not implement arbitrary statistical testing in V1. Do not compute or display statistics that are invalid for the question type. Suppress small subgroup filters that could identify respondents.

8.10 Intervention/impact project workspace

Tabs:

Overview

Theory of Change

Team

Tasks

Milestones

Evidence

Metrics

Updates

Mentor Review

Impact Report

Proposal fields:

linked problem and research;

target users;

proposed intervention;

why it should help;

theory of change;

supporting evidence;

team and mentor;

timeline;

risks;

resources.

Theory of change structure:

problem → intervention → immediate output → expected change → measurable outcome

Tasks are lightweight, with title, description, assignee, status, priority, due date, and optional milestone. Use statuses BACKLOG, TODO, IN_PROGRESS, REVIEW, and DONE. Do not build a complex Jira clone.

8.11 Metrics and baseline gate

Require:

exactly one primary metric;

up to three secondary metrics;

metric name, description, unit, direction, collection method, and target;

a baseline plan before project approval;

a baseline observation before the intervention becomes active unless an authorized reviewer records a justified exception.

Observation phases:

BASELINE

DURING

POST

FOLLOW_UP

Each observation stores value, date, sample size when relevant, recorder, notes, and linked evidence.

The results UI may calculate an absolute and percentage change where valid, but language must say observed change. Do not automatically claim that the intervention caused the change.

8.12 Impact report

Generate an editable, versioned report with:

Problem

Evidence

Research Question

Intervention

Theory of Change

Implementation

Primary and Secondary Metrics

Results

What Changed

Limitations

What Did Not Work

Negative or Inconclusive Findings

Next Steps

Evidence Appendix

Review and Official Response History

Allow negative and inconclusive reports to complete the workflow. Do not reward only positive outcomes.

8.13 Mentor review queue

Show exception-based queues:

needs review;

privacy warning;

methodology warning;

missing metric;

missing baseline;

due soon;

stale work;

changes resubmitted.

Each item must show why it appears, owner/team, due date or last activity, linked entity, and next decision.

Review detail supports:

contextual artifact snapshot;

comments tied to a section;

approve;

request changes with required reason;

comment without state change;

review history and artifact version.

8.14 Moderation queue

Tabs:

private review;

visibility decisions;

duplicate suggestions;

archived/closed.

Sensitive record handling:

restricted access;

prominent urgent-help route;

sensitivity reason without making an allegation of truth;

route to designated staff;

record decision, actor, time, and reason.

Duplicate handling:

show new report and up to three cluster candidates;

show similarity explanation and compatible metadata;

allow open-both, merge, not-a-match, and undo merge;

require a reason;

preserve the original report and evidence.

AI flags or suggests. A human moderator decides.

8.15 OSIS and official responses

OSIS sees only allowed non-sensitive summaries and aggregates. Provide:

emerging clusters;

validated clusters without action;

active OSIS-linked interventions;

response history;

official update composer when authorized.

Official updates are append-only versions with status, message, author, and time. Corrections create a new version rather than silently editing history.

8.16 Admin settings and audit

Admin configuration includes:

school name and branding;

grades and classes;

categories;

role assignments;

allowed pilot categories;

moderation defaults;

review requirements;

stale-project threshold;

file restrictions;

urgent-help notice;

retention-policy reference;

publication policy;

UI language setting.

Audit viewer supports filters by actor, action, entity, and date. Do not store raw sensitive content in audit metadata.

9. Workflow state machines

Implement validated transition services. Do not permit arbitrary status strings.

Problem report

DRAFT → SUBMITTED → PRIVATE_REVIEW | MODERATION_REVIEW → PUBLISHED | MERGED | ARCHIVED

Problem cluster

NEW → GATHERING_EVIDENCE → VALIDATED → UNDER_INVESTIGATION
→ ACTION_PLANNED → ACTION_UNDERWAY → RESOLVED
→ IMPACT_MEASURED → CLOSED

Research project

DRAFT → MENTOR_REVIEW → CHANGES_REQUESTED | APPROVED
→ COLLECTING → ANALYZING → COMPLETED → ARCHIVED

Survey

DRAFT → REVIEW_REQUIRED → APPROVED → OPEN → CLOSED → ARCHIVED

Impact project

DRAFT → REVIEW → CHANGES_REQUESTED | APPROVED
→ ACTIVE → PAUSED | COMPLETED → IMPACT_REVIEW
→ PUBLISHED | ARCHIVED

All status changes require:

valid current and target state;

actor permission;

reason when required;

timestamp;

audit event;

notification to relevant users.

10. Database model

Use UUID primary keys, timezone-aware timestamps, explicit foreign keys, indexes for common filters, and soft archive fields where appropriate. Add school_id to all school-owned entities.

Identity and configuration

schools

users

memberships

roles

role_assignments

invitations

grades

classes

categories

school_settings

Problem discovery

problem_reports

problem_clusters

problem_cluster_memberships

problem_signals

cluster_status_history

official_updates

Evidence and research

files

evidence_items

research_projects

research_plan_versions

research_variables

claims

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

moderation_flags

ai_runs

audit_logs

Essential constraints

Unique problem signal per (user_id, cluster_id, signal_type).

One active cluster membership per problem report.

Exactly one primary metric per impact project.

No more than three active secondary metrics in V1.

Approved research-plan, survey, and impact-report versions are immutable.

Survey question position is unique within a version.

Metric unit cannot change after baseline without a new metric/version.

Anonymous response exports contain no user ID, name, email, or reversible token.

Status transitions occur only through domain services.

Deactivating a user does not delete authored history.

Model raw reports separately from curated clusters. Never overwrite the author's original report when merging.

11. API contract

Use /api/v1, UUID path identifiers, typed request/response schemas, cursor pagination for feeds, consistent errors, and optimistic concurrency/version checks for editable artifacts.

Error envelope:

{
  "error": {
    "code": "RESEARCH_PLAN_INCOMPLETE",
    "message": "Complete the required sections before mentor review.",
    "field_errors": {"limitations": "Required"},
    "request_id": "..."
  }
}

Implement these API groups:

POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/me
POST   /api/v1/invitations/{token}/accept

POST   /api/v1/problem-reports
GET    /api/v1/problem-reports/{id}
PATCH  /api/v1/problem-reports/{id}
POST   /api/v1/problem-reports/{id}/submit
GET    /api/v1/problem-clusters
GET    /api/v1/problem-clusters/{id}
POST   /api/v1/problem-clusters/{id}/signals
DELETE /api/v1/problem-clusters/{id}/signals/{type}
POST   /api/v1/problem-clusters/{id}/evidence
POST   /api/v1/moderation/problem-reports/{id}/visibility-decision
POST   /api/v1/moderation/problem-reports/{id}/merge
POST   /api/v1/moderation/problem-reports/{id}/unmerge

POST   /api/v1/research-projects
GET    /api/v1/research-projects/{id}
PUT    /api/v1/research-projects/{id}/plan
POST   /api/v1/research-projects/{id}/submit-review
POST   /api/v1/research-projects/{id}/claims
POST   /api/v1/research-projects/{id}/evidence

POST   /api/v1/surveys
GET    /api/v1/surveys/{id}
PUT    /api/v1/surveys/{id}/draft
POST   /api/v1/surveys/{id}/submit-review
POST   /api/v1/surveys/{id}/publish
POST   /api/v1/surveys/{id}/close
GET    /api/v1/public/surveys/{code}
POST   /api/v1/public/surveys/{code}/responses
GET    /api/v1/surveys/{id}/analysis
GET    /api/v1/surveys/{id}/export

POST   /api/v1/impact-projects
GET    /api/v1/impact-projects/{id}
PATCH  /api/v1/impact-projects/{id}
POST   /api/v1/impact-projects/{id}/submit-review
POST   /api/v1/impact-projects/{id}/activate
POST   /api/v1/impact-projects/{id}/tasks
PATCH  /api/v1/tasks/{id}
POST   /api/v1/impact-projects/{id}/milestones
POST   /api/v1/impact-projects/{id}/metrics
POST   /api/v1/impact-metrics/{id}/observations
GET    /api/v1/impact-projects/{id}/report
PUT    /api/v1/impact-projects/{id}/report

POST   /api/v1/reviews
POST   /api/v1/problem-clusters/{id}/official-updates
GET    /api/v1/notifications
POST   /api/v1/notifications/{id}/read
GET    /api/v1/mentor/attention
GET    /api/v1/osis/overview
GET    /api/v1/admin/audit-logs
GET    /api/v1/admin/settings
PUT    /api/v1/admin/settings

Generate OpenAPI documentation and keep frontend types synchronized with backend schemas through generation or contract tests.

12. Authentication and security

For the closed alpha, implement invite-only accounts. Use the existing school identity provider only if already configured and authorized.

Requirements:

no public self-registration;

secure HTTP-only cookie session or correctly implemented short-lived token flow;

adaptive password hashing if local passwords are used;

CSRF protection for cookie-based mutations;

strict CORS configuration;

rate limiting for login, invitations, survey submission, file upload, and AI endpoints;

secrets outside source control;

safe account deactivation;

permission tests for every role and sensitive resource;

user-generated content encoded/sanitized against stored XSS;

no raw survey response or sensitive report text in logs;

request IDs and structured redacted logging.

13. Privacy and safeguarding

Do not collect date of birth, home address, personal phone number, parent information, government IDs, medical records, or disciplinary records.

Potential bullying, harassment, abuse, self-harm, crisis, personal accusation, or individual staff/student complaint must never publish automatically. Route it to restricted review and show the configured school help route.

The product is not an emergency reporting system. State this clearly without discouraging students from seeking help.

For anonymous-public reports, hide the identity from students while allowing only designated staff to access it if policy permits. Log such access.

For anonymous surveys:

separate eligibility/one-response enforcement from researcher-visible response data;

do not expose identity mappings to project teams;

suppress risky small-subgroup filters;

warn that free text may self-identify;

protect exports with authorization and audit events.

File handling:

allowlist file types;

enforce configurable size limits;

use generated storage object names;

validate MIME type and extension;

provide short-lived authorized downloads;

scan files when a scanner is available;

never trust the user-provided filename;

ensure private-file URLs cannot be guessed or reused by unauthorized users.

14. AI architecture

Do not build one giant chatbot. Implement narrow services:

Problem extractor and clarification helper.

Sensitive-content first-pass flagger.

Duplicate suggestion engine.

Research-question helper.

Methodology explanation helper.

Survey wording critic.

Impact-language guard.

Mentor-attention explanation.

Every LLM call must:

use a versioned prompt;

send only necessary fields;

request strict JSON;

validate through Pydantic;

retry invalid structured output at most once;

store provider/model, prompt version, duration, success/failure, and safe metadata;

show output as a suggestion or warning;

record accepted, edited, dismissed, or escalated outcome;

fail without blocking the manual flow.

Never store secrets or full sensitive inputs in ai_runs.

Suggested problem-extraction schema

{
  "category_suggestion": "ACADEMICS",
  "problem_type": "assessment_workload",
  "affected_group": "Grade 10 students",
  "scope": "several classes",
  "observable_claims": ["Major assignments share the same three-day window"],
  "missing_information": ["frequency", "observation period"],
  "clarifying_questions": [
    "During which weeks did this occur?",
    "Approximately how many major assignments shared the same period?"
  ],
  "sensitivity_flags": [],
  "confidence": 0.78
}

Duplicate engine

Normalize report text.

Create an embedding asynchronously.

Search active clusters within the same school and compatible categories.

Combine semantic similarity with grade, scope, and category compatibility.

Return at most three candidates.

Show why each candidate may match.

Require a moderator to merge.

Store moderator match/not-match outcomes for future evaluation, not immediate custom training.

Use configurable thresholds and allow no suggestion when confidence is low.

Deterministic methodology rules

Implement versioned rules for:

research question too broad;

multiple outcomes in one question;

missing population;

missing operational definition;

convenience sample generalized beyond its population;

leading or loaded wording;

double-barrelled question;

ambiguous wording;

sensitive information without justification;

mean used for unsuitable categories;

conclusion exceeds the observed population;

correlation or before/after observation described as causation;

primary metric declared after intervention data exists.

Each warning needs:

stable rule ID;

severity;

triggering field/text reference;

student-friendly explanation;

suggested correction;

rule version;

acknowledgement or resolution status.

15. Seed data

Create idempotent seed scripts with clearly synthetic examples.

Demo users:

student@demo.local

leader@demo.local

mentor@demo.local

osis@demo.local

moderator@demo.local

admin@demo.local

Use safe demo authentication documented in the README and enabled only in DEMO.

Seed:

20–30 individual reports;

8–12 clusters;

at least one private report visible only to designated roles;

all four structured signal types;

5–8 research projects across different states;

3–5 surveys with synthetic responses;

4 impact projects across draft, review, active, and impact-review states;

one positive, one negative, and one inconclusive result;

mentor attention items;

official update history;

representative audit events.

Use one complete golden-path scenario throughout:

Problem: Assessment Workload Concentration
Research: How concentrated are major assignment deadlines across Grade 10 classes during a typical month?
Intervention: Shared Assessment Calendar
Primary metric: Number of major deadlines inside a three-day window
Baseline: synthetic pre-intervention count
Post: synthetic post-intervention count
Conclusion: observed change with limitations, not a causal claim

Display Synthetic demonstration data wherever users might otherwise mistake it for a real Pilar finding.

16. Notifications and audit

Create in-app notifications for:

review requested;

changes requested;

approval;

invitation to team;

task assigned or due soon;

problem status change;

official update;

survey opened or closed;

project blocked by a missing baseline;

moderation decision relevant to the author.

Audit at minimum:

role/account changes;

access to restricted reports;

visibility decisions;

cluster merge/unmerge;

research, survey, intervention, and impact review decisions;

survey publish, close, and export;

metric/baseline creation or change;

project activation exception;

official update publication;

archive and data export actions.

17. Accessibility, responsiveness, and performance

Requirements:

keyboard navigation;

visible focus styles;

semantic headings and landmarks;

labels and described form errors;

text alternatives for icons;

WCAG AA color contrast where practical;

charts paired with accessible summaries or tables;

no status communicated through color alone;

survey flow usable on a typical phone screen;

loading skeletons or progress states without layout jumps;

useful error recovery.

Pilot targets:

normal API p95 under 800 ms excluding AI;

feeds/search p95 under 1.5 seconds;

survey response acknowledgement under 1 second in normal conditions;

AI target under 10 seconds with visible progress and manual continuation;

responsive initial page under 3 seconds on ordinary school Wi-Fi after authentication.

Do not sacrifice correctness or privacy merely to hit a synthetic benchmark.

18. Testing requirements

Backend unit tests

permission policies;

state-transition services;

unique signals;

survey validation and calculations;

methodology rules;

baseline activation gate;

impact wording guard;

anonymized export serializer.

Backend integration tests

invitation/login and deactivation;

normal versus private report submission;

visibility decision;

cluster merge and unmerge;

research review versioning;

survey approve, publish, respond, close, and export;

impact proposal approval and activation;

metric observations;

official update history;

audit-event creation.

Frontend tests

form validation and error display;

role-based route protection;

AI suggestion accept/edit/dismiss;

blocked-action explanation;

survey builder behavior;

review decision UI;

private visibility labels;

responsive navigation.

Playwright end-to-end flows

Student submits a normal measurable problem; moderator publishes and merges it.

Student submits a potentially sensitive report; it never appears in the student feed.

Leader creates research, receives changes, revises, and gains approval.

Mentor approves a survey; an anonymous respondent submits; researcher sees only authorized data.

Project activation is blocked until primary metric, baseline plan, and baseline observation exist.

Team records post measurement and submits an impact report; mentor requests changes and then approves.

OSIS/admin publishes an official update.

AI provider is unavailable and the manual golden path still completes.

Security tests

one student cannot read another restricted draft;

students cannot call mentor/moderator/admin endpoints;

mentors cannot read unassigned private work;

anonymous exports contain no identity leakage;

stored XSS payloads are not executed;

survey replay is idempotent;

private file downloads reject unauthorized access;

audit logs exclude raw sensitive content.

19. Implementation order

Work in this order and keep the application runnable after each milestone.

Milestone 1 — Foundation

monorepo/tooling;

database and migrations;

authentication/invitations;

roles and permission services;

application shell;

demo-mode banner;

seed users;

CI and base tests.

Milestone 2 — Voice vertical slice

problem wizard;

private routing;

problems index and cluster page;

structured signals;

evidence metadata/files;

manual moderation and merging;

state history and official updates;

AI clarification and duplicate suggestions after manual flow works.

Milestone 3 — Research vertical slice

research plan and versions;

methodology rules;

mentor review;

evidence/claim mapping;

survey builder;

approved survey version;

response flow;

basic analysis and safe export.

Milestone 4 — Impact vertical slice

intervention proposal;

theory of change;

project team;

tasks and milestones;

metrics and baseline gate;

observations and before/after display;

impact report and review.

Milestone 5 — Role workspaces and hardening

role-aware dashboards;

mentor attention queue;

OSIS workspace;

admin settings and audit viewer;

notifications;

accessibility;

security hardening;

backup/restore documentation;

golden-path Playwright tests.

20. Definition of done

The closed alpha is complete only when:

the full golden path works through the database;

every P0 button performs a real action;

normal and sensitive report paths are tested;

private reports cannot leak through feeds, counts, search, files, or APIs;

all five roles have backend permission tests;

approved research plans, survey versions, and reports retain version history;

anonymous response export has been tested for identity leakage;

project activation enforces the metric and baseline gate;

negative and inconclusive results can be published internally;

AI unavailability does not block the workflow;

seed data is labeled synthetic;

migrations apply cleanly from an empty database;

frontend lint, type check, tests, and production build pass;

backend lint/type checks where configured and pytest pass;

README explains setup, demo accounts, architecture, commands, environment variables, limitations, and unresolved Pilar policy decisions;

no secrets, real student records, or invented real school findings are committed.

21. Required final handoff

When implementation finishes, report:

what was completed by milestone;

which core flows were manually verified;

test, type-check, lint, build, and migration results;

demo account instructions;

required environment variables;

architecture and important design decisions;

known limitations and deferred V2 features;

unresolved school-policy decisions that prevent live deployment;

the safest next action.

Do not describe the application as live-school-ready until the school discovery and governance decisions are completed.

Start by inspecting the repository and producing a short implementation-status audit. Then implement the milestones in order. Do not stop after creating plans or static mockups when the repository authorizes implementation.

PROMPT END