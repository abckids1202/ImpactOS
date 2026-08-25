from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import _RATE_LIMITS, app
from app.db import SessionLocal
from app.models import AuthSession, Invitation
from app.security import token_hash


@pytest.fixture
def client():
    with TestClient(app) as value:
        yield value


@pytest.fixture(autouse=True)
def reset_rate_limits():
    _RATE_LIMITS.clear()
    yield
    _RATE_LIMITS.clear()


def csrf_headers(client: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": client.cookies.get("impactos_csrf", "")}


def login(client: TestClient, email: str, password: str = "demo1234") -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def test_login_refresh_logout_and_server_revocation(client: TestClient) -> None:
    result = login(client, "student@demo.local")
    assert result["user"]["roles"] == ["STUDENT_CONTRIBUTOR"]
    raw_session = client.cookies.get("impactos_session")
    assert raw_session
    with SessionLocal() as db:
        row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(raw_session)))
        assert row is not None
        assert raw_session not in row.token_hash

    refreshed = client.get("/api/v1/auth/me")
    assert refreshed.status_code == 200
    assert refreshed.json()["user"]["email"] == "student@demo.local"
    logged_out = client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    assert logged_out.status_code == 200
    after_logout = client.get("/api/v1/auth/me")
    assert after_logout.status_code == 401
    assert after_logout.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_invalid_credentials_are_generic_and_rate_limited(client: TestClient) -> None:
    _RATE_LIMITS.clear()
    first = client.post("/api/v1/auth/login", json={"email": "missing@example.test", "password": "wrong"})
    second = client.post("/api/v1/auth/login", json={"email": "student@demo.local", "password": "wrong"})
    assert first.status_code == second.status_code == 401
    assert first.json()["error"]["code"] == second.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert "request_id" in first.json()["error"]
    for _ in range(8):
        client.post("/api/v1/auth/login", json={"email": "missing@example.test", "password": "wrong"})
    limited = client.post("/api/v1/auth/login", json={"email": "missing@example.test", "password": "wrong"})
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
    _RATE_LIMITS.clear()


def test_expired_session_is_rejected(client: TestClient) -> None:
    login(client, "student@demo.local")
    raw_session = client.cookies.get("impactos_session")
    with SessionLocal() as db:
        row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(raw_session)))
        assert row is not None
        row.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"


def test_invitation_states_and_single_use(client: TestClient) -> None:
    pending = client.get("/api/v1/auth/invitations/verify?token=demo-pending-invitation-token")
    assert pending.status_code == 200
    assert pending.json()["state"] == "ACTIVE"
    assert pending.json()["roles"] == ["STUDENT_CONTRIBUTOR"]
    assert client.get("/api/v1/auth/invitations/verify?token=demo-expired-invitation-token").json()["error"]["code"] == "INVITATION_EXPIRED"
    assert client.get("/api/v1/auth/invitations/verify?token=demo-revoked-invitation-token").json()["error"]["code"] == "INVITATION_REVOKED"

    email = f"phase1-{uuid4().hex[:10]}@example.test"
    admin = TestClient(app)
    try:
        login(admin, "admin@demo.local")
        created = admin.post("/api/v1/admin/invitations", headers=csrf_headers(admin), json={"email": email, "roles": ["MENTOR"], "expires_in_days": 2})
        assert created.status_code == 200, created.text
        raw = created.json()["token"]
        with SessionLocal() as db:
            row = db.get(Invitation, created.json()["id"])
            assert row is not None and raw not in row.token_hash and row.token_hash == token_hash(raw)
        mismatch = client.post(f"/api/v1/auth/activate?token={raw}", json={"email": "wrong@example.test", "display_name": "Wrong", "password": "alpha-password-123", "password_confirmation": "alpha-password-123"})
        assert mismatch.status_code == 400
        assert mismatch.json()["error"]["code"] == "INVITATION_EMAIL_MISMATCH"
        accepted = client.post(f"/api/v1/auth/activate?token={raw}", json={"email": email, "display_name": "Phase One Mentor", "password": "alpha-password-123", "password_confirmation": "alpha-password-123"})
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["user"]["roles"] == ["MENTOR"]
        reused = client.get(f"/api/v1/auth/invitations/verify?token={raw}")
        assert reused.status_code == 410
        assert reused.json()["error"]["code"] == "INVITATION_USED"
    finally:
        admin.close()


def test_multirole_union_and_admin_boundaries(client: TestClient) -> None:
    multi = login(client, "multi@demo.local")["user"]
    assert set(multi["roles"]) == {"STUDENT_PROJECT_LEADER", "MENTOR"}
    assert {"app.access", "profile.read_own", "research_project.manage", "mentor.review"}.issubset(set(multi["permissions"]))
    assert client.get("/api/v1/admin/members").status_code == 403

    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    login(client, "moderator@demo.local")
    forbidden = client.post("/api/v1/admin/invitations", headers=csrf_headers(client), json={"email": "not-created@example.test", "role": "STUDENT", "expires_in_days": 1})
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "PERMISSION_DENIED"


def test_admin_deactivation_revokes_existing_member_session(client: TestClient) -> None:
    admin = TestClient(app)
    member = TestClient(app)
    email = f"deactivate-{uuid4().hex[:10]}@example.test"
    try:
        login(admin, "admin@demo.local")
        created = admin.post("/api/v1/admin/invitations", headers=csrf_headers(admin), json={"email": email, "role": "STUDENT", "expires_in_days": 2})
        assert created.status_code == 200, created.text
        token = created.json()["token"]
        activated = member.post(f"/api/v1/auth/activate?token={token}", json={"email": email, "display_name": "Deactivated Member", "password": "alpha-password-123", "password_confirmation": "alpha-password-123"})
        assert activated.status_code == 200, activated.text
        assert member.get("/api/v1/auth/me").status_code == 200
        members = admin.get("/api/v1/admin/members").json()
        target = next(row for row in members if row["email"] == email)
        response = admin.post(f"/api/v1/admin/members/{target['membership_id']}/deactivate", headers=csrf_headers(admin))
        assert response.status_code == 200, response.text
        assert member.get("/api/v1/auth/me").status_code == 401
        assert member.get("/api/v1/auth/me").json()["error"]["code"] == "ACCOUNT_DEACTIVATED"
    finally:
        admin.close()
        member.close()
