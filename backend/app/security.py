from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .db import get_db
from .models import User


SECRET_KEY = os.getenv("IMPACTOS_SECRET_KEY", "closed-alpha-local-secret-change-me").encode()
SESSION_COOKIE = "impactos_session"
CSRF_COOKIE = "impactos_csrf"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180_000)
    return f"pbkdf2$180000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
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


def _encode(value: dict[str, Any]) -> str:
    body = base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(SECRET_KEY, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def _decode(token: str) -> dict[str, Any] | None:
    try:
        body, signature = token.split(".", 1)
        expected = hmac.new(SECRET_KEY, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padded = body + "=" * (-len(body) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if int(data.get("exp", 0)) < int(time.time()):
            return None
        return data
    except (ValueError, json.JSONDecodeError, TypeError):
        return None


def create_session(user: User) -> tuple[str, str]:
    token = _encode({"sub": user.id, "school_id": user.school_id, "exp": int(time.time()) + 60 * 60 * 12})
    return token, secrets.token_urlsafe(24)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token and request.headers.get("Authorization", "").startswith("Bearer "):
        token = request.headers["Authorization"][7:]
    data = _decode(token) if token else None
    user = db.get(User, data.get("sub")) if data else None
    if not user or not user.active or data.get("school_id") != user.school_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in is required.")
    return user


def require_csrf(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid.")


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission for this action.")
        return user

    return dependency
