# ImpactOS Phase 1 — Authentication and Access Foundation

## Local run

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python scripts\migrate.py
python scripts\seed_demo.py
cd frontend
npm install
npm run dev
```

Run the API in a second terminal with `uvicorn app.main:app --app-dir backend --reload --port 8000`. The Vite development proxy sends `/api` requests to the API. The readiness endpoint is `GET /api/v1/ready`.

For an existing alpha database, `scripts/migrate.py` applies the additive compatibility columns. The checked-in Alembic revision is the staging migration record: run `alembic upgrade head` after the existing base schema has been provisioned.

## Demo-only access

When `APP_MODE=DEMO` and `DEVELOPMENT_SEED_ENABLED=true`, the seed creates synthetic accounts. The default demo password is `demo1234` (override it with `DEMO_PASSWORD`). Accounts include `student@demo.local`, `mentor@demo.local`, `moderator@demo.local`, `admin@demo.local`, and `multi@demo.local`. The pending invitation token is `demo-pending-invitation-token`.

These credentials and raw invitation tokens must never be enabled in a production environment.

## Phase 1 routes

Public/auth routes are `/login`, `/activate`, `/forgot-password`, and `/reset-password/:token`. Protected workspace routes are `/app`, `/app/profile`, `/app/mentor`, `/app/osis`, `/app/moderation`, `/app/admin/members`, `/app/admin/invitations`, and `/app/admin/audit`. Unauthorized role access goes to `/unauthorized`.

All authenticated mutations require the CSRF cookie/header pair. Session cookies are HTTP-only, SameSite=Lax, and Secure in production. Configure `IMPACTOS_SECRET_KEY`, `COOKIE_SECURE=true`, explicit `CORS_ORIGINS`, and a real database before deployment.
