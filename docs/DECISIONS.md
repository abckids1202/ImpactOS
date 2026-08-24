# ImpactOS Implementation Decisions

Updated: 24 August 2026

These are implementation decisions for the synthetic closed alpha. They are not substitutes for Pilar policy approval.

| Decision | Current choice | Reason / consequence |
|---|---|---|
| Local database | SQLite by default | Zero-setup development; SQLAlchemy configuration accepts PostgreSQL through `DATABASE_URL`. |
| Primary API | FastAPI + SQLAlchemy | Matches the definitive plan and keeps domain checks testable. |
| Frontend | React + TypeScript + Vite | Keeps the app shell and API-backed workflow easy to run locally. |
| Authentication | Invite-only-style demo login with signed HTTP-only session cookie | No public registration; synthetic demo accounts are easy to test. |
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

- The current single `User.role` field is enough for the first synthetic alpha; production needs school-scoped role assignments.
- `scripts/migrate.py` uses SQLAlchemy metadata creation for the zero-setup alpha; a full Alembic migration history should be added before staging.
- The local session signer is suitable for development only; production needs managed secrets and deployment configuration.
- The deterministic sensitivity and methodology checks are fixtures, not a safeguarding decision engine.
- The public institution copy, official contact/support route, verified-school-email domain, mail provider, and publication approver still require Pilar confirmation.
