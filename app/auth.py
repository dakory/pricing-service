from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_database_session
from app.models import AdminSession

# Cookie names are centralized so deployments can audit and rename them safely.
SESSION_COOKIE = "pricing_session"
CSRF_COOKIE = "pricing_csrf"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_token(value: str) -> str:
    """Return a non-reversible SHA-256 hash for a session token."""

    return hashlib.sha256(value.encode()).hexdigest()


def verify_admin(email: str, password: str) -> bool:
    """Compare submitted credentials with the configured single administrator."""

    settings = get_settings()
    return hmac.compare_digest(email.lower(), settings.admin_email.lower()) and hmac.compare_digest(
        password, settings.admin_password
    )


def create_session(response: Response, db: Session) -> None:
    """Persist an administrator session and attach secure cookies."""

    settings = get_settings()
    session_id = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    db.add(
        AdminSession(
            id=hash_token(session_id),
            csrf_token_hash=hash_token(csrf),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
    )
    db.commit()
    cookie = dict(secure=settings.cookie_secure, samesite="strict", path="/", max_age=43_200)
    response.set_cookie(SESSION_COOKIE, session_id, httponly=True, **cookie)
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **cookie)


def clear_session(response: Response) -> None:
    """Remove authentication cookies from the response."""

    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


def require_session(
    request: Request,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_database_session),
) -> AdminSession:
    """Require and return a valid, unexpired administrator session."""

    if not session_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    session = db.get(AdminSession, hash_token(session_cookie))
    now = datetime.now(timezone.utc)
    if not session or session.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return session


def require_csrf(
    request: Request,
    session: AdminSession = Depends(require_session),
    csrf_cookie: str | None = Cookie(default=None, alias=CSRF_COOKIE),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> AdminSession:
    """Require a matching CSRF cookie and header for unsafe methods."""

    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
        if not hmac.compare_digest(session.csrf_token_hash, hash_token(csrf_header)):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
    return session
