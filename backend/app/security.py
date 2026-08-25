from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from .db import get_db
from .models import AuthSession, Membership, Role, RoleAssignment, School, User


SESSION_COOKIE = os.getenv("SESSION_COOKIE_NAME", "impactos_session")
CSRF_COOKIE = "impactos_csrf"
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", str(60 * 60 * 12)))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
PASSWORD_HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

ROLE_ALIASES = {
    "STUDENT": "STUDENT_CONTRIBUTOR",
    "STUDENT_LEADER": "STUDENT_PROJECT_LEADER",
    "MENTOR": "MENTOR",
    "OSIS": "OSIS_REVIEWER",
    "MODERATOR": "MODERATOR",
    "ADMIN": "ADMINISTRATOR",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "STUDENT_CONTRIBUTOR": {"app.access", "profile.read_own", "profile.update_own", "problem_report.create"},
    "STUDENT_PROJECT_LEADER": {"app.access", "profile.read_own", "profile.update_own", "problem_report.create", "research_project.manage"},
    "MENTOR": {"app.access", "profile.read_own", "profile.update_own", "mentor.review"},
    "OSIS_REVIEWER": {"app.access", "profile.read_own", "profile.update_own", "osis.review"},
    "MODERATOR": {"app.access", "profile.read_own", "profile.update_own", "moderation.review"},
    "ADMINISTRATOR": {
        "app.access", "profile.read_own", "profile.update_own", "admin.members.read", "admin.members.manage",
        "admin.invitations.manage", "admin.audit.read", "problem_report.create", "research_project.manage",
        "mentor.review", "osis.review", "moderation.review",
    },
}


def normalize_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role)


def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    """Verify Argon2id hashes and accept pre-Phase-1 PBKDF2 hashes during upgrade."""
    if encoded.startswith("$argon2"):
        try:
            return PASSWORD_HASHER.verify(encoded, password)
        except (VerifyMismatchError, VerificationError, InvalidHash):
            return False
    try:
        scheme, rounds, salt_b64, digest_b64 = encoded.split("$", 3)
        if scheme != "pbkdf2":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def password_needs_upgrade(encoded: str) -> bool:
    return not encoded.startswith("$argon2id$")


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def cookie_secure() -> bool:
    return COOKIE_SECURE or os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower() in {"production", "prod"}


def validate_security_config() -> None:
    environment = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
    if environment in {"production", "prod"}:
        if not cookie_secure():
            raise RuntimeError("COOKIE_SECURE=true is required in production.")
        if os.getenv("IMPACTOS_SECRET_KEY", "").strip() in {"", "closed-alpha-local-secret-change-me"}:
            raise RuntimeError("IMPACTOS_SECRET_KEY must be configured in production.")


def create_session(user: User, db: DbSession, request: Request | None = None) -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(48)
    csrf = secrets.token_urlsafe(32)
    user_agent = request.headers.get("user-agent", "")[:255] if request else None
    ip_hash = hashlib.sha256((request.client.host if request and request.client else "").encode()).hexdigest() if request else None
    db.add(AuthSession(id=secrets.token_hex(16), user_id=user.id, token_hash=token_hash(raw_token), expires_at=datetime.utcnow() + timedelta(seconds=SESSION_TTL_SECONDS), ip_hash=ip_hash, user_agent=user_agent))
    return raw_token, csrf


def session_cookie_options() -> dict[str, Any]:
    return {"httponly": True, "samesite": "lax", "secure": cookie_secure(), "max_age": SESSION_TTL_SECONDS}


def get_current_user(request: Request, db: DbSession = Depends(get_db)) -> User:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "AUTHENTICATION_REQUIRED", "message": "Sign in is required."})
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(raw_token)))
    session_user = db.get(User, session.user_id) if session else None
    if session_user and (not session_user.active or getattr(session_user, "status", "ACTIVE") != "ACTIVE"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "ACCOUNT_DEACTIVATED", "message": "This account is deactivated. Contact a school administrator."})
    now = datetime.utcnow()
    if not session or session.revoked_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "SESSION_REVOKED", "message": "This session is no longer active. Please sign in again."})
    if session.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "SESSION_EXPIRED", "message": "Your session expired. Please sign in again."})
    user = session_user
    if not user or not user.active or getattr(user, "status", "ACTIVE") != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "ACCOUNT_DEACTIVATED", "message": "This account is not active."})
    school = db.get(School, user.school_id)
    if school and not getattr(school, "is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "ACCOUNT_DEACTIVATED", "message": "This school workspace is not active."})
    session.last_seen_at = now
    request.state.auth_session = session
    return user


def revoke_session(session: AuthSession) -> None:
    session.revoked_at = datetime.utcnow()


def revoke_all_sessions(db: DbSession, user_id: str) -> int:
    sessions = db.scalars(select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))).all()
    for session in sessions:
        revoke_session(session)
    return len(sessions)


def active_role_codes(db: DbSession, user: User) -> list[str]:
    codes: set[str] = set()
    membership = db.scalar(select(Membership).where(Membership.user_id == user.id, Membership.school_id == user.school_id, Membership.status == "ACTIVE"))
    if membership:
        rows = db.execute(select(Role.code).join(RoleAssignment, RoleAssignment.role_id == Role.id).where(RoleAssignment.membership_id == membership.id, RoleAssignment.revoked_at.is_(None))).all()
        codes.update(row[0] for row in rows)
        # The legacy users.role value is only a compatibility fallback. Once a
        # membership has role assignments, the assignments are authoritative so
        # an administrator can actually remove an old role.
        if not codes and user.role:
            codes.add(normalize_role(user.role))
    elif user.role:
        codes.add(normalize_role(user.role))
    return sorted(codes)


def active_permissions(db: DbSession, user: User) -> list[str]:
    permissions: set[str] = set()
    for role in active_role_codes(db, user):
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return sorted(permissions)


def require_roles(*roles: str):
    allowed = {normalize_role(role) for role in roles}

    def dependency(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> User:
        if not allowed.intersection(active_role_codes(db, user)):
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "You do not have permission for this action."})
        return user

    return dependency


def require_permissions(*permissions: str):
    required = set(permissions)

    def dependency(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)) -> User:
        if not required.issubset(set(active_permissions(db, user))):
            raise HTTPException(status_code=403, detail={"code": "PERMISSION_DENIED", "message": "You do not have permission for this action."})
        return user

    return dependency


def require_csrf(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail={"code": "CSRF_INVALID", "message": "The security check failed. Refresh the page and try again."})
