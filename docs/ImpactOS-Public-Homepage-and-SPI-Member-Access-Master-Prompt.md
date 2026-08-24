ImpactOS — Public Homepage and SPI Member Access Master Implementation Prompt

Project: ImpactOS / Pilar Impact Lab
Institution: Sekolah Pilar Indonesia (SPI)
Purpose: Replace the login-only first impression with a formal public website, controlled SPI member activation, working authentication, and protected application routing.
Date: 24 August 2026

Copy-ready prompt

You are the lead full-stack engineer responsible for the next milestone of the existing ImpactOS / Pilar Impact Lab application for Sekolah Pilar Indonesia (SPI).

The current application exposes a login/demo screen as the root experience. It contains demo credentials and currently displays a raw Not Found error when login is attempted. This makes the application look like an unfinished internal tool and gives public visitors no formal explanation of its purpose.

Implement a complete separation between:

a polished public institutional website for visitors;

controlled SPI member authentication and account activation; and

the existing protected ImpactOS application.

This is an implementation task, not another planning-only task. Inspect the repository first, preserve existing working features, diagnose the real authentication failure, then implement and verify the complete milestone.

1. Product objective

The finished application must communicate two identities clearly:

Sekolah Pilar Indonesia is the institution.

Pilar Impact Lab, powered by ImpactOS, is the school's problem-to-impact platform.

Public visitors should understand what the platform does without signing in:

ImpactOS helps the SPI community identify meaningful problems, validate them with evidence, investigate them responsibly, develop interventions, and measure what honestly changed.

Members of SPI should then be able to sign in or activate an approved account to enter the protected platform.

The public website must feel formal, credible, welcoming, and connected to SPI. The protected application must remain private and role-controlled.

2. Non-negotiable rules

Inspect the current frontend and backend before modifying routes.

Do not delete or rewrite working protected ImpactOS features.

Diagnose and fix the existing login Not Found error before declaring authentication complete.

Do not leave the existing demo account list publicly visible outside development/demo mode.

Do not implement unrestricted public registration.

A visitor may view public institutional information but may never view internal reports, evidence, research drafts, survey data, mentor comments, moderation data, users, or audit logs.

Public impact stories must use a separate explicitly approved and sanitized public representation.

Do not expose an internal entity by merely hiding fields in the frontend. Public data boundaries must be enforced by backend endpoints and allowlisted serializers.

Do not invent real facts about SPI, such as accreditation, enrollment numbers, achievements, contact details, programs, addresses, or statistics.

Use approved institutional content or configurable placeholders for facts that have not been supplied.

Do not hotlink or scrape images from the official school website. Use repository-owned approved assets or intentional placeholders.

Keep APP_MODE=DEMO, CLOSED_ALPHA, and PRODUCTION behavior distinct.

Do not deploy or use real student data unless explicitly authorized.

Every visible button in this milestone must work or be clearly marked as unavailable with a reason.

Run tests, type checks, linting, migrations, and production builds before finishing.

3. Repository audit and authentication diagnosis

Before implementation, produce a concise internal audit covering:

current frontend framework and route tree;

current backend framework and API prefix;

authentication method;

session/token storage strategy;

current login request URL and HTTP method;

configured frontend API base URL;

development proxy configuration;

backend router mounting;

CORS and CSRF configuration;

existing registration/invitation code;

existing protected routes;

current tests and commands;

whether the worktree already contains user changes.

Diagnose the current Not Found error

Trace the login action from the form to the backend. Check, at minimum:

whether the frontend calls /auth/login, /api/auth/login, or /api/v1/auth/login;

whether the backend actually exposes the same route and method;

whether the FastAPI router is included in main.py;

whether the frontend development proxy strips or duplicates /api;

whether an environment variable points to the wrong host or prefix;

whether static SPA fallback is incorrectly handling an API call;

whether a trailing slash or method mismatch exists;

whether Docker/container hostnames differ from browser-accessible hostnames;

whether the frontend converts every 404 into the same raw Not Found message.

Fix the root cause. Do not mask it with a fake success response or hardcoded demo login.

After the fix:

add an automated backend login test;

add a frontend login integration test with a mocked or test backend;

add one end-to-end test that logs in and reaches the correct protected dashboard;

return friendly typed errors rather than raw backend text;

log a safe request ID without logging passwords.

Document the root cause in the final handoff.

4. Target route architecture

Use three distinct layout groups.

4.1 Public routes — PublicLayout

/
/about
/how-it-works
/impact
/impact/:slug
/safety-and-privacy
/faq
/contact

These routes are accessible without authentication and must never require an auth API call to render their core content.

4.2 Authentication routes — AuthLayout

/login
/activate
/register                 compatibility alias to /activate
/invite/:token
/verify-email
/forgot-password
/reset-password/:token

Use Activate SPI Account as the primary public wording instead of generic open registration.

4.3 Protected routes — AppLayout

Place all internal ImpactOS routes under /app:

/app/dashboard
/app/problems
/app/problems/new
/app/problems/reports/:reportId
/app/problems/:clusterId
/app/research
/app/research/:researchId
/app/research/:researchId/survey
/app/research/:researchId/analysis
/app/projects
/app/projects/:projectId
/app/projects/:projectId/impact
/app/tasks
/app/notifications
/app/settings
/app/mentor
/app/osis
/app/moderation
/app/admin
/app/admin/users
/app/admin/configuration
/app/admin/audit

4.4 Backward compatibility

If internal routes currently exist without /app, add controlled redirects where safe:

/dashboard        → /app/dashboard
/problems         → /app/problems
/research         → /app/research
/projects         → /app/projects
/mentor           → /app/mentor
/osis             → /app/osis
/moderation       → /app/moderation
/admin            → /app/admin

Preserve query parameters and safe route state. Do not redirect an unauthenticated user directly past authentication.

4.5 Authentication redirects

Unauthenticated access to a protected route redirects to /login?next=<encoded-path>.

After successful login, return to next only if it is an internal relative path beginning with /app/.

Reject absolute URLs, protocol-relative URLs, encoded external URLs, JavaScript schemes, and malformed values.

If next is absent or unsafe, use /app/dashboard.

Authenticated users opening /login or /activate should be offered Open Dashboard rather than another auth form.

Logout clears the server session, invalidates local auth state, and returns to / with a non-sensitive confirmation.

5. Public visual identity

Create a visual system that feels connected to a respected school institution while keeping Pilar Impact Lab distinct from the main school website.

Use the official SPI website only as a general reference for institutional tone and hierarchy. Do not clone its implementation or copy large portions of its text.

5.1 Design direction

Formal, calm, modern, and human.

More open and visually rich than the internal dashboard.

Not a startup SaaS template.

Not childish, cartoonish, or filled with floating decorative shapes.

Avoid glassmorphism, excessive gradients, excessive pill elements, and dozens of empty cards.

Use generous whitespace and clear section rhythm.

Use authentic approved campus/student imagery only when available.

If approved photography is unavailable, use restrained geometric or editorial placeholders rather than unrelated stock images.

5.2 Suggested palette

Reuse or harmonize with the current ImpactOS navy/teal system:

Institutional navy:      #0D2942
Deep teal:               #1F5D64
Primary teal:            #2E7478
Soft teal surface:       #EAF4F3
Warm paper background:   #F7F6F1
White surface:           #FFFFFF
Main text:               #172433
Muted text:              #5E6C76
Border:                  #D8E0E2
Success:                 #2F6B4F
Warning:                 #A66A13
Danger/private:          #943F46

Use existing project tokens if equivalent. Do not introduce conflicting one-off colors.

5.3 Typography

Use a clean institutional sans-serif already available in the project, or load one responsibly.

Use a confident large hero heading without making every section oversized.

Body text must remain at least 16px on public pages where practical.

Keep line lengths readable, roughly 60–75 characters for prose.

Avoid all-uppercase paragraphs.

Eyebrow labels may use restrained uppercase and letter spacing.

5.4 Public shell

Desktop header:

left: approved SPI logo if present, otherwise a refined text lockup;

identity: Pilar Impact Lab;

secondary label: Sekolah Pilar Indonesia or Powered by ImpactOS;

center navigation;

right actions: Member Login and Activate Account;

sticky after scrolling, with compact height and subtle border/shadow.

Mobile header:

brand lockup;

accessible menu button;

drawer containing all navigation and both member actions;

focus trap, Escape close, restored focus, and body-scroll control.

Footer:

Pilar Impact Lab identity;

short purpose statement;

public navigation;

member access;

safety/privacy;

link to the official SPI website;

configurable institutional/contact information;

pilot status where applicable;

copyright year generated correctly.

6. Public homepage specification — /

Build a complete homepage, not only a hero section.

6.1 Announcement or pilot strip

In DEMO or CLOSED_ALPHA, show a restrained strip:

Pilar Impact Lab is currently being developed and tested with synthetic data.

Do not display internal demo credentials in this strip.

In production, this strip must be configurable or removable.

6.2 Hero section

Eyebrow:

PILAR IMPACT LAB · SEKOLAH PILAR INDONESIA

Primary heading:

From student concerns to measurable change.

Supporting text:

Pilar Impact Lab helps the SPI community identify meaningful problems, investigate them responsibly, develop practical interventions, and measure what genuinely changed.

Primary CTA:

Explore How It Works → /how-it-works

Secondary CTA for signed-out visitors:

SPI Member Login → /login

Secondary CTA for authenticated members:

Open Dashboard → /app/dashboard

Include a subtle workflow visual showing:

Discover → Research → Act → Measure

Do not use fake statistics or fabricated student testimonials.

6.3 Institutional introduction

Heading:

A clearer path from observation to action

Explain that important observations often become disconnected conversations, while student projects may begin before the problem is properly understood. ImpactOS connects the process into a traceable, evidence-based journey.

Use three supporting principles:

Evidence over popularity — structured signals and evidence replace simple likes.

Human judgment remains central — AI assists, while students, mentors, OSIS, and school staff decide.

Honest outcomes — negative or inconclusive results are still valuable learning.

6.4 Four-stage workflow

Create four connected cards or a horizontal/vertical timeline:

Discover

Students describe observable problems, identify who is affected, and contribute evidence.

Research

Teams form responsible questions, design surveys, examine evidence, and document limitations.

Act

Approved research becomes a practical intervention with a theory of change, team, and plan.

Measure

Teams record a baseline before acting, compare later observations, and publish what was learned.

Each stage links to the relevant section of /how-it-works.

6.5 Role section

Heading:

One system, different responsibilities

Include five role cards:

Students: report, support, investigate, and participate.

Project Leaders: organize research, interventions, metrics, and reports.

Teachers and Mentors: review methodology and focus attention where judgment is needed.

OSIS: understand non-sensitive school-wide needs and communicate progress.

School Administrators: protect privacy, moderate sensitive material, and maintain accountability.

Role cards must explain value, not list internal permissions exhaustively.

6.6 Public impact stories preview

Heading:

Learning through measurable action

Display up to three approved public stories.

Each story card may contain only:

approved title;

problem summary;

intervention summary;

approved observed result;

limitation summary;

status;

publication date;

generic team label if authorized;

approved cover asset.

If there are no published stories, show a thoughtful empty state:

Public impact stories will appear here after projects complete review and receive publication approval.

Never fill this section with invented real SPI projects. Synthetic demo stories must show an obvious Synthetic example label and must not be indexable as real outcomes.

CTA:

View Approved Impact Stories → /impact

6.7 AI and human governance section

Explain the boundary clearly:

AI helps students clarify problems, detect possible duplicates, improve research questions, and recognize unsupported claims. It does not decide whether a person is guilty, approve a project, publish a report, or make school policy.

Use a two-column comparison:

AI may assist                         Humans remain responsible
Clarify wording                       Decide visibility
Suggest related problems              Merge or reject duplicates
Explain methodology warnings          Approve research and surveys
Flag unsupported conclusions          Review and publish outcomes

6.8 Safety and privacy section

Explain:

sensitive reports use restricted review;

public pages never expose internal student submissions or survey responses;

only minimum member information is collected;

approved public impact stories are sanitized separately;

ImpactOS is not an emergency-reporting service;

the school-configured urgent-help route is available to members where appropriate.

CTA:

Read Safety and Privacy → /safety-and-privacy

6.9 Member access callout

Heading:

Part of the SPI community?

Copy:

Sign in to continue your projects, contribute evidence, review assigned work, or follow school initiatives. New accounts require verified SPI membership or an invitation.

Buttons:

Member Login

Activate SPI Account

Authenticated state:

Replace both with Open Dashboard.

6.10 Frequently asked questions preview

Include accessible accordion questions:

What is Pilar Impact Lab?

Who can use the internal platform?

Can anyone see student problem reports?

Does AI make school decisions?

What happens when a report is sensitive?

Can a project publish a negative result?

Link to the full FAQ page.

7. Additional public pages

7.1 About — /about

Include:

relationship between Pilar Impact Lab, ImpactOS, and SPI;

platform vision;

the problem the platform addresses;

product principles;

intended pilot status;

link to the official SPI website for formal information about the school.

Do not duplicate or pretend to replace the school's official website.

7.2 How it works — /how-it-works

Explain the complete internal journey in public-safe language:

Discover
→ Clarify and Route
→ Validate
→ Research
→ Collect Evidence
→ Propose
→ Record Baseline
→ Implement
→ Measure
→ Review
→ Publish Approved Learning

For each stage, show:

purpose;

participating roles;

output;

human checkpoint;

privacy note when relevant.

Do not show internal private screenshots containing student data.

7.3 Public impact index — /impact

Features:

approved published stories only;

search approved title/summary;

filters for category, year, status, and result type;

pagination;

empty state;

Synthetic example filtering and labeling in demo mode;

no sorting by student popularity;

no internal project IDs exposed when a public slug can be used.

7.4 Public impact detail — /impact/:slug

Allowed sections:

approved problem statement;

approved evidence summary;

approved research question;

intervention;

measurement approach;

observed result;

limitations;

what did not work;

next steps;

official response if approved;

publication/review statement.

Do not expose:

raw evidence;

raw survey answers;

team private workspace;

individual student names without explicit policy authorization;

mentor comments;

internal audit history;

private identifiers;

attachments not separately approved for publication.

7.5 Safety and privacy — /safety-and-privacy

Include public plain-language explanations of:

what information is public;

what information remains internal;

private/sensitive report routing;

survey privacy principles;

AI boundaries;

data minimization;

publication approval;

emergency-channel limitation;

configurable school contact/help route;

contact for corrections or privacy concerns, using approved configuration only.

Avoid presenting placeholder text as actual school policy. Mark unresolved areas as pilot policy pending confirmation.

7.6 FAQ — /faq

Use categories:

About the platform;

Membership;

Privacy;

Research and projects;

AI;

Public impact stories.

Make FAQ content data-driven rather than hardcoded into one large component.

7.7 Contact — /contact

For V1, prefer a safe informational page with approved contact channels rather than an unauthenticated arbitrary message form.

If no approved contact is configured, show:

Contact information will be published after the school confirms the pilot support route.

Do not invent an email address.

8. Member login experience

Redesign /login so it is clearly part of the formal platform rather than the homepage.

Layout

Use a split layout on desktop:

left: concise product identity, privacy reassurance, and link back to the public homepage;

right: focused login card.

On mobile, use a single column.

Fields and actions

Email

Password

Show/hide password

Remember this device only if securely supported

Sign in

Forgot password

Activate SPI Account

Back to homepage

Behavior

Disable submit only while request is active or fields are invalid.

Preserve email after an authentication error, but never preserve password.

Use friendly errors:

We couldn't sign you in with those details.

Your account is awaiting approval.

Your account has been deactivated. Contact the designated SPI administrator.

The member service is temporarily unavailable. Please try again.

Do not reveal whether a specific unknown email exists.

Do not display raw Not Found, stack traces, response bodies, or internal routes.

Display a request/reference ID only for support when available.

Rate-limit repeated attempts.

Ensure keyboard submission and password-manager compatibility.

Demo mode

When APP_MODE=DEMO and the environment is not production:

show a clear synthetic-data notice;

optionally expose a collapsed Demo access panel;

label every account synthetic;

never reuse production credentials;

never show demo access controls when production environment detection is true, even if a client-side variable is manipulated.

The backend must enforce demo-mode availability; client-side hiding alone is insufficient.

9. SPI member activation and registration

Do not provide open self-registration where anyone can claim to be an SPI member.

Use configurable controlled activation methods.

9.1 Supported paths

Invitation activation — required V1 path

Administrator creates an invitation for a specific email and initial role.

System stores a hashed, single-use, expiring token.

User opens /invite/:token.

Backend validates token without consuming it.

User sees invited email in masked form where appropriate.

User sets display name and password and accepts the public privacy notice.

Final submission consumes token atomically, creates/activates membership, and starts or offers login.

Used, expired, revoked, or invalid token receives a safe state and recovery instruction.

Approved school-email activation — configurable

Only implement active self-service email activation when an administrator has configured approved SPI email domains.

User enters school email.

Backend normalizes email and checks the domain server-side.

Return the same neutral response whether eligible or not, preventing email enumeration.

Send a single-use verification link through configured email provider.

Verified accounts receive only the safest default role, usually STUDENT, or enter PENDING_APPROVAL depending on settings.

Users cannot select mentor, OSIS, moderator, or administrator roles themselves.

If no approved domain or mail provider exists, do not simulate delivery in production. Explain that an administrator invitation is required.

Access request — optional and disabled by default

If implemented, collect only email, name, member type, and a short reason. Protect with rate limits and moderation. It creates a pending request, not an account.

9.2 Activation page content

Heading: Activate your SPI member account

Explain eligibility.

Offer invitation token flow.

Offer school-email flow only when configured.

Link existing members to login.

Explain that privileged roles are assigned by authorized staff.

Link public privacy information.

9.3 Security requirements

hashed tokens at rest;

token expiry;

single use;

revocation;

atomic consumption;

password strength rules based on length and compromised-password protection when available;

adaptive password hashing;

rate limits;

email enumeration resistance;

no role escalation from request body;

audit invitation creation, revocation, acceptance, and role assignment;

invalidate active sessions after security-sensitive account changes when appropriate.

10. Authentication backend contract

Use or adapt the existing backend conventions. Prefer /api/v1 if that is already the product standard.

Required endpoints:

POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/session
GET  /api/v1/me

POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password

GET  /api/v1/invitations/{token}/preview
POST /api/v1/invitations/{token}/accept

POST /api/v1/activation/request-email
GET  /api/v1/activation/verify-email

POST /api/v1/admin/invitations
GET  /api/v1/admin/invitations
POST /api/v1/admin/invitations/{id}/revoke

Do not return password hashes, raw tokens, sensitive account state, or unnecessary membership details.

Session choice

Prefer secure server-managed sessions or properly implemented short-lived access tokens with refresh rotation. Do not store long-lived bearer tokens in localStorage.

For cookie sessions:

HttpOnly;

Secure in appropriate environments;

suitable SameSite policy;

CSRF protection for state-changing requests;

session rotation after login;

invalidation on logout;

expiration and idle timeout.

Error format

Use a consistent typed envelope:

{
  "error": {
    "code": "AUTHENTICATION_FAILED",
    "message": "We couldn't sign you in with those details.",
    "field_errors": {},
    "request_id": "safe-reference-id"
  }
}

Frontend maps error codes to friendly text. It must not surface arbitrary server bodies.

11. Public content architecture

Do not build a full CMS during this milestone.

Use two content sources:

11.1 Stable institutional content

Store headings, descriptions, FAQ entries, navigation, official-site URL, contact placeholders, and feature flags in a typed public content/config module or backend site-settings endpoint.

Requirements:

easy to update without editing many components;

supports English now and future Indonesian localization;

no secrets;

validated schema;

fallbacks that do not invent school facts;

production build does not include internal-only configuration.

11.2 Public impact stories

Use database-backed explicit publication records.

Recommended table:

public_impact_stories
---------------------
id UUID
school_id UUID
source_project_id UUID nullable/restricted
slug string unique per school
title string
problem_summary text
evidence_summary text nullable
research_question text nullable
intervention_summary text
measurement_summary text
observed_result text
limitations text
what_did_not_work text nullable
next_steps text nullable
official_response text nullable
category_id UUID nullable
result_type enum POSITIVE | NEGATIVE | INCONCLUSIVE | MIXED
status enum DRAFT | REVIEW | APPROVED | PUBLISHED | WITHDRAWN
cover_file_id UUID nullable
public_team_label string nullable
is_synthetic boolean
approved_by UUID nullable
approved_at timestamp nullable
published_by UUID nullable
published_at timestamp nullable
withdrawn_at timestamp nullable
created_at timestamp
updated_at timestamp
version integer

Important:

Public story content is copied/sanitized into explicit fields; it is not a live unrestricted view of the internal project.

Publishing requires authorized approval.

Withdrawing immediately removes it from public endpoints but preserves governance history.

Edits after approval create a new review requirement or version.

Public slugs do not expose internal UUIDs unnecessarily.

Cover assets require independent publication approval.

Required public endpoints:

GET /api/v1/public/site
GET /api/v1/public/impact-stories
GET /api/v1/public/impact-stories/{slug}
GET /api/v1/public/faq

Required authorized management endpoints:

POST  /api/v1/admin/public-impact-stories
PATCH /api/v1/admin/public-impact-stories/{id}
POST  /api/v1/admin/public-impact-stories/{id}/submit-review
POST  /api/v1/admin/public-impact-stories/{id}/approve
POST  /api/v1/admin/public-impact-stories/{id}/publish
POST  /api/v1/admin/public-impact-stories/{id}/withdraw

If admin authoring is too large for the current milestone, implement backend fixtures and read-only public endpoints first, but preserve the explicit approval model and do not expose internal projects directly.

12. Public data-boundary rules

Create dedicated public response schemas. Never return ORM objects directly.

Public endpoints may return only explicit allowlisted fields.

Test that public endpoints cannot reveal:

user IDs;

student names or emails;

grade/class membership unless specifically approved aggregate content;

internal project IDs;

raw problem reports;

report authors;

private visibility values;

evidence storage keys or private URLs;

survey IDs, raw answers, respondent hashes, or subgroup data;

internal review comments;

moderation flags;

AI-run inputs/outputs;

audit metadata;

unpublished or withdrawn content.

Create negative authorization and serialization tests for every category above.

13. Frontend architecture

Use the existing React/Vite architecture if present.

Suggested feature structure:

src/
├── layouts/
│   ├── PublicLayout.tsx
│   ├── AuthLayout.tsx
│   └── AppLayout.tsx
├── features/
│   ├── public-site/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   ├── content/
│   │   └── schemas/
│   ├── auth/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   ├── guards/
│   │   └── schemas/
│   └── app/
├── routes/
├── components/
└── styles/

Required shared components:

PublicHeader

MobileNavigation

PublicFooter

MemberActionButtons

HeroWorkflow

WorkflowStageCard

RoleValueCard

ImpactStoryCard

PublicSafetyCallout

FaqAccordion

AuthCard

PasswordField

ProtectedRoute

RoleRoute

DemoModeBanner

PublicEmptyState

PageMeta

Avoid one enormous homepage component. Keep sections composable and content-driven.

Authentication state bootstrapping

On application startup, request session state once through a query/provider.

Public pages render even if the auth service is temporarily unavailable.

Auth-dependent CTA may show a neutral loading state briefly, but must not block public content.

Protected routes wait for session resolution before redirecting.

Clear cached protected queries on logout.

Do not flash protected content before permission resolution.

14. SEO and public-web requirements

Because the homepage is intended for strangers and formal public information, implement:

meaningful document titles;

page-specific meta descriptions;

canonical URLs from configuration;

Open Graph and social preview metadata using approved assets;

robots.txt behavior by environment;

sitemap for public pages only;

semantic headings;

descriptive link text;

favicon/brand asset configuration;

noindex for login, activation, reset-password, demo impact stories, and all /app routes;

no sensitive values in URLs or page metadata.

In DEMO or non-production deployments, default the entire site to noindex unless explicitly configured otherwise.

If adding Organization/School JSON-LD, populate it only with administrator-approved factual configuration. Do not invent structured data.

15. Accessibility and responsive requirements

WCAG AA contrast where practical.

Keyboard-accessible navigation, CTAs, accordions, forms, and mobile drawer.

Visible focus state.

Skip-to-content link.

Semantic header, nav, main, section, and footer landmarks.

One clear H1 per page.

Form labels and programmatic error descriptions.

Error summary for failed activation/registration where useful.

aria-expanded and aria-controls for menus/accordions.

Reduced-motion behavior.

No autoplay video.

Images require appropriate alt text; decorative images use empty alt.

Touch targets large enough for mobile.

Public layout tested at approximately 360px, 768px, 1024px, and wide desktop widths.

Avoid horizontal scrolling.

Preserve usable navigation at 200% zoom.

16. Performance requirements

Do not require the protected application bundle to render the public homepage when route-level splitting is feasible.

Lazy-load non-critical public sections and protected route groups appropriately.

Optimize approved images and provide responsive sizes.

Avoid large animation libraries for simple effects.

Prevent layout shift by reserving media space.

Public pages must not wait for AI services.

Cache stable public content appropriately without caching private sessions publicly.

Handle public API failure with graceful content fallbacks.

Target a fast first render on ordinary school/mobile connections.

17. Security requirements

Strict server-side authorization for all protected endpoints.

Separate public and internal serializers.

Rate-limit login, activation, invitation preview/acceptance, forgot-password, and public search.

Validate and normalize email server-side.

Prevent open redirects through next.

Prevent user-controlled role assignment.

Use safe session cookies or correctly rotated token strategy.

CSRF protection for cookie-authenticated mutations.

Strict CORS allowlist.

Content Security Policy appropriate to deployed assets.

Frame-ancestor/clickjacking protection.

Referrer policy.

MIME sniffing protection.

Sanitize/encode public story content.

Validate public slugs.

Avoid exposing environment variables in frontend builds.

Do not log credentials, raw tokens, password reset links, or sensitive internal content.

Audit activation, login security events, invitations, public publication, withdrawal, and restricted data access.

18. Testing requirements

18.1 Backend tests

Test:

correct login route exists and works;

wrong credentials return neutral error;

deactivated and pending accounts are handled;

logout invalidates session;

invitation preview, expiry, revocation, single use, and atomic acceptance;

email activation domain checks when configured;

user cannot choose privileged role;

rate limits;

safe password reset flow;

public site endpoint contains allowlisted fields only;

unpublished and withdrawn stories never appear publicly;

published story serializer contains no internal identifiers;

anonymous/public user cannot access any /app API;

open redirect attempts fail safely;

demo authentication is disabled in production.

18.2 Frontend tests

Test:

public homepage renders without authentication;

all public navigation links work;

mobile navigation is keyboard accessible;

signed-out header shows login and activation;

signed-in header shows dashboard;

login form maps backend errors correctly;

raw Not Found is never rendered;

protected routes redirect with safe next;

unsafe next is discarded;

authenticated user returns to requested safe protected page;

registration method visibility follows configuration;

demo controls appear only in allowed mode;

empty impact-stories state works;

public impact cards label synthetic examples;

FAQ accordion is accessible;

page metadata is correct.

18.3 End-to-end tests

A stranger opens /, navigates public pages, and never triggers a protected-data response.

A stranger opens /app/problems, is redirected to login, signs in, and returns to /app/problems.

A malicious next=https://example.com attempt returns safely to /app/dashboard.

An invited student activates an account and signs in.

A student cannot select or assign themselves a privileged role.

A production-mode visitor cannot see demo credentials or switch roles.

A published impact story is visible; a draft and withdrawn story are not.

An unauthenticated request for an internal problem, survey, file, or user is rejected.

Logout clears protected state and back navigation does not reveal cached private content.

Authentication backend unavailable: public homepage still renders and login shows a helpful service error.

18.4 Visual checks

Manually inspect:

public homepage desktop and mobile;

long navigation labels;

no impact stories;

three impact stories;

long title/summary wrapping;

demo banner;

logged-in versus logged-out header;

login error;

expired invitation;

keyboard focus sequence;

200% zoom;

dark browser/system contrast differences if relevant.

19. Implementation order

Follow this order and keep the project runnable after every step.

Phase 1 — Audit and authentication repair

inspect repository;

reproduce login Not Found;

identify root cause;

align API route/base URL/proxy;

add typed errors;

add backend/frontend/E2E authentication tests.

Exit condition: a demo or test member can sign in and reach the protected dashboard through the real backend.

Phase 2 — Route separation

introduce PublicLayout, AuthLayout, and AppLayout;

move/protect internal routes under /app;

add safe compatibility redirects;

implement session bootstrapping and safe next handling;

verify logout and cached-state clearing.

Exit condition: public and protected route trees behave correctly for signed-in and signed-out states.

Phase 3 — Public shell and homepage

implement design tokens;

public header/mobile navigation/footer;

homepage sections;

config-driven content;

authenticated CTA switching;

responsive/accessibility pass.

Exit condition: a stranger can understand the product and reach member access without viewing internal content.

Phase 4 — Additional public pages

About;

How It Works;

Safety and Privacy;

FAQ;

Contact;

metadata, sitemap, robots behavior.

Exit condition: formal public information exists beyond the homepage and contains no invented school claims.

Phase 5 — Member activation

invitation creation/preview/acceptance;

activation page;

configurable school-email activation if genuinely supported;

forgot/reset password;

rate limits and audit behavior;

administrator invitation management.

Exit condition: a new approved SPI member can securely activate an account without public role escalation.

Phase 6 — Public impact stories

database/migration;

public-safe schemas and endpoints;

list/detail UI;

publication/withdrawal workflow or controlled fixtures;

synthetic labeling;

privacy leakage tests.

Exit condition: only explicitly published sanitized stories appear publicly.

Phase 7 — Hardening and handoff

security headers;

performance/code splitting;

full accessibility review;

all automated tests;

migrations from empty database;

production build;

documentation and screenshots if the repository workflow supports them.

Exit condition: every definition-of-done item below passes.

20. Definition of done

This milestone is complete only when:

/ is a complete formal public homepage;

public About, How It Works, Impact, Safety/Privacy, FAQ, and Contact pages exist;

the existing login Not Found bug has a documented root cause and verified fix;

a real backend login reaches a protected route;

public, auth, and protected route groups are separated;

safe post-login redirects work;

unrestricted public registration does not exist;

invitation-based account activation works;

privileged roles cannot be self-selected;

demo credentials and role switching cannot appear in production;

public endpoints use dedicated allowlisted schemas;

no internal report, survey, evidence, member, review, moderation, file, or audit data leaks publicly;

impact stories require explicit publication and can be withdrawn;

no fabricated SPI fact is presented as official;

public pages are responsive, keyboard accessible, and properly labeled;

login/activation errors are helpful and never expose raw backend messages;

public SEO metadata and non-production noindex behavior work;

migrations apply from an empty database;

backend tests pass;

frontend lint, type check, tests, and production build pass;

required end-to-end flows pass;

documentation explains routes, authentication, invitation activation, content configuration, environment variables, demo behavior, and remaining school-policy decisions.

21. Required final handoff

At completion, report:

repository architecture discovered;

exact root cause of the original login Not Found error;

files and routes changed;

public pages implemented;

authentication and activation behavior;

public/private data boundary implementation;

database migration details;

configuration and environment variables;

demo versus production behavior;

test, lint, type-check, build, and migration results;

manual responsive/accessibility checks;

limitations and deferred work;

policy/content values still awaiting SPI confirmation;

safest next development milestone.

Do not describe the feature as complete merely because the homepage looks correct. Authentication, registration control, public-data isolation, route guards, responsive behavior, and automated verification are all part of this milestone.

Begin by inspecting the repository and reproducing the login failure. Then implement the phases sequentially and verify each exit condition before continuing.

