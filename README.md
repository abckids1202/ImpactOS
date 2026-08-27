# ImpactOS — Pilar Impact Lab Closed Alpha

ImpactOS is a school workflow application that helps students move from a real problem to evidence, a practical intervention, and an honest account of what changed.

This repository now contains the closed-alpha implementation baseline and the planning package. It runs with synthetic demonstration data and is not approved for live student data until the school-policy blockers are resolved.

## Current implementation

- FastAPI + SQLAlchemy backend in `backend/`.
- SQLite zero-setup development database; PostgreSQL is supported through `DATABASE_URL`.
- Public Pilar Impact Lab site with separate `/`, `/about`, `/how-it-works`, `/impact`, `/safety-and-privacy`, `/faq`, and `/contact` routes.
- Controlled SPI member access under `/login`, `/activate`, `/invite/:token`, `/forgot-password`, and `/reset-password/:token`; protected workspace routes live under `/app/*`.
- Invite-only-style demo accounts with signed HTTP-only sessions and CSRF protection. Demo access is disabled when `APP_MODE=PRODUCTION` or `ENVIRONMENT=production`.
- Explicit public impact-story records and allowlisted serializers; internal reports, identities, evidence, surveys, moderation, and audit data never cross the public API boundary.
- React + TypeScript + Vite frontend in `frontend/`.
- Role-aware member workspace with centralized navigation and dashboards for student contributors, project leaders, mentors, OSIS reviewers, moderators, and administrators. Each workspace exposes only the records and actions allowed by the signed-in membership.
- Connected closed-alpha scenario for “Long canteen queues during the second break,” including student reports and follows, moderation decisions, a versioned research plan, mentor review, an OSIS priority/update draft, an impact project, and assigned tasks.
- Real API-backed workflows for dashboard, problem reports, private moderation, clusters, signals, evidence, research plans, mentor review, surveys, analysis/export, impact projects, metrics, baseline activation, observations, impact reports, OSIS overview, notifications, and audit logs.
- Synthetic seed data also retains the original golden path: Assessment Workload Concentration → Deadline research → Shared Assessment Calendar → observed change.
- Pilar Civic Lab UI foundation: semantic light/dark themes, responsive app shell with mobile navigation, sticky public navigation, editorial public styling, accessible focus states, reduced-motion support, loading/empty/error surfaces, and consistent status/button/form treatments.
- Workspace utilities: authorized record search with keyboard shortcuts (`Ctrl/Cmd+K` or `/`), offline status notice, back-to-top control, in-app feedback submission, and an administrator feedback triage queue. Feedback stores safe context only and never includes passwords, session tokens, or private record contents.
- ImpactOS Response Loop: `Report → Problem Cluster → Evidence → Decision → Commitment → Update → Result → Next Action`, with a visible next-step panel and safe problem timeline.
- Problem-to-Action Ledger: published problems expose accountable ownership, next-update dates, intended outcomes, response status, and completion evidence without using likes, votes, popularity, or opaque AI scores.
- Two-lane unified work view at `/app/tasks`: project tasks remain separate from school response commitments, while owners and managers can post updates and complete commitments only with a completion note or evidence reference.
- Response commitment API and migration: `ResponseCommitment`, member-visible updates, audited ownership transfers/status changes, `NOT_NOW` reason and review-date validation, evidence-led priority assessments, and in-app due/reminder/quiet attention states.
- Synthetic canteen response commitment seeded for the closed alpha; existing problem clusters are never assigned invented owners during migration and remain in the review queue until a real owner is recorded.
- Planning and discovery artifacts in `docs/`.

### UI polish boundary

This phase intentionally delivers the Response Loop vertical slice while preserving the existing API-backed workflows and permission model. Friction Radar, representation/evidence-coverage warnings, school response templates, student civic portfolios, and cross-school learning remain sequenced follow-on work. The repository also does not yet include production file storage, so drag-and-drop evidence uploads, upload progress, offline write queues, and draft autosave remain deferred. Full notification preferences, saved/recent records, command-palette actions beyond search, PWA installation, localization, and automated browser visual regression are also follow-on work for the closed alpha.

## Run locally

Prerequisites: Python 3.9+, Node.js 18+, and npm. Docker is optional; SQLite is the default local database.

### Terminal 1 — backend

From `C:\Users\charl\OneDrive\Desktop\ImpactOS`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python scripts\migrate.py
python scripts\seed_demo.py
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

If PowerShell blocks activation, run the Python commands without activation using `.venv\Scripts\python.exe`.

Backend URLs:

- API health: <http://127.0.0.1:8000/api/v1/health>
- OpenAPI docs: <http://127.0.0.1:8000/docs>

### Terminal 2 — frontend

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

The public homepage is the default route. The member workspace is available at <http://localhost:5173/login>; successful login safely returns to an internal `/app/*` destination only. The previous login `Not Found` error was caused by the frontend retaining `/login` after authentication while the old authenticated route map only recognized legacy top-level workspace paths. The new route transition sends members to `/app/dashboard` and keeps legacy paths as redirects.

For a public production build, set `VITE_PUBLIC_INDEX=true` before `npm run build`. Local and closed-alpha builds use `noindex,nofollow`; update `frontend/public/robots.txt` and the sitemap only after the school confirms the public launch decision.

### Controlled activation

There is no open registration. An administrator creates a single-use invitation through the protected admin API, then shares the returned activation path through the approved school channel. The verified-school-email endpoint currently returns a neutral response and intentionally does not pretend to send mail; connect a managed mail provider only after Pilar confirms the domain, retention, support route, and safeguarding policy.

Public API endpoints are `GET /api/v1/public/site`, `GET /api/v1/public/faq`, `GET /api/v1/public/impact-stories`, and `GET /api/v1/public/impact-stories/{slug}`.

### Response Loop endpoints

The closed-alpha workflow exposes problem browsing/detail/timeline/work under `/api/v1/problems`, plus response commitment creation, updates, transfers, completion, the unified work composition, and priority assessment. See the generated OpenAPI document at `/docs` for request and permission details. Project tasks remain in their existing table and endpoints; `/api/v1/work` composes both lanes without replacing them.

## Demo accounts

All demo accounts use password `demo1234`:

| Role | Email |
|---|---|
| Student contributor | `student@demo.local` |
| Student project leader | `leader@demo.local` |
| Mentor | `mentor@demo.local` |
| OSIS reviewer | `osis@demo.local` |
| Moderator | `moderator@demo.local` |
| Administrator | `admin@demo.local` |

The app displays a persistent `DEMO DATA` label. Demo-role switching is intentionally limited to the login screen and synthetic data.

## Verification commands

```powershell
python -m pytest backend\tests -q
cd frontend
npm test -- --run
npm run lint
npm run build
```

The first backend start creates `impactos.db` in the current working directory. To rebuild synthetic data locally, stop the backend and remove only that file, then rerun `scripts\migrate.py` and `scripts\seed_demo.py`.

## Key documents

- `docs/ImpactOS-Definitive-Build-Plan-and-Master-Prompt.md` — definitive implementation plan.
- `docs/ImpactOS-V1-PRD-and-System-Specification.md` — product and system baseline.
- `docs/DECISIONS.md` — implementation decisions and assumptions.
- `docs/LIVE_DEPLOYMENT_BLOCKERS.md` — policy decisions required before live school use.
- `docs/ImpactOS-Public-Homepage-Design-Addendum.md` — public homepage and access requirements addendum.
- `docs/ImpactOS-Public-Homepage-and-SPI-Member-Access-Master-Prompt.md` — full public homepage/member-access build prompt.
- `docs/discovery/` — interview and prototype-test materials.
- `docs/wireframes/` — low-fidelity specifications and the earlier browsable prototype.

## Architecture notes

Routes validate input and delegate state changes through explicit transition maps. Every high-value mutation records an audit event. Restricted reports are filtered server-side, and anonymous survey responses deliberately do not store a researcher-visible identity. AI behavior is currently represented by deterministic, explainable demo suggestions; the manual workflow never depends on an AI provider.

Response commitments are intentionally separate from project execution tasks. Managers can see school-level response work, while members only see assigned or school-visible records; overdue attention is a quiet queue state and is never attached publicly to an individual.

This is a closed-alpha baseline, not a production deployment. The next safe action is to run the seeded golden path, execute the automated checks, and then use the discovery pack to confirm Pilar's safeguarding, authority, authentication, retention, contact, verified-email, and public-publication decisions.
