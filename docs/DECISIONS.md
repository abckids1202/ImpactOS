# ImpactOS Implementation Decisions

Updated: 25 August 2026

These are implementation decisions for the synthetic closed alpha. They are not substitutes for Pilar policy approval.

| Decision | Current choice | Reason / consequence |
|---|---|---|
| Local database | SQLite by default | Zero-setup development; SQLAlchemy configuration accepts PostgreSQL through `DATABASE_URL`. |
| Primary API | FastAPI + SQLAlchemy | Matches the definitive plan and keeps domain checks testable. |
| Frontend | React + TypeScript + Vite | Keeps the app shell and API-backed workflow easy to run locally. |
| Authentication | Invite-only activation plus opaque, database-backed HTTP-only sessions | No public registration; Argon2id password hashes, server-side revocation, and multi-role memberships are testable and production-aligned. |
| Route boundary | Public and auth pages at the root; all protected workspace pages under `/app/*` | Prevents accidental exposure of member UI and provides a stable safe redirect target. |
| Public stories | Separate `PublicImpactStory` records with an allowlisted serializer | A public story is an explicit publication decision, not a view over internal project data. |
| Activation | Single-use hashed invitation tokens; neutral verified-email and password-recovery responses | Avoids account enumeration and does not claim that email delivery exists before a provider is configured. |
| CSRF | Double-submit cookie/header check on authenticated mutations | Required because the alpha uses cookie sessions. |
| AI | Deterministic demo adapter first | AI failure cannot block manual workflow; provider integration is deferred behind schemas. |
| File uploads | Evidence metadata first; file abstraction remains a next hardening step | Avoids accepting unscanned student files before storage/security policy is configured. |
| State changes | Explicit transition maps in `backend/app/main.py` | Prevents arbitrary status strings and makes invalid actions testable. |
| Anonymous surveys | Response rows store no respondent identity in anonymous mode | Protects researcher-visible anonymity in the closed-alpha path. |
| Seed data | Synthetic Pilar-shaped records | The app is clearly labeled `DEMO DATA`; no real school findings are implied. |

## Assumptions to revisit

- `User.role` remains only as a legacy compatibility field; `Membership` + `RoleAssignment` is authoritative for Phase 1 access decisions.
- `scripts/migrate.py` remains the zero-setup local bootstrap; the checked-in Alembic migration is the staging migration path after the base schema exists.
- Sessions store only a SHA-256 token hash in the database; production still needs managed secrets, HTTPS, secure cookies, and deployment configuration.
- The deterministic sensitivity and methodology checks are fixtures, not a safeguarding decision engine.
- The public institution copy, official contact/support route, verified-school-email domain, mail provider, and publication approver still require Pilar confirmation.
