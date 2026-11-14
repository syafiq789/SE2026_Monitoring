import hashlib
import secrets
from datetime import datetime, timedelta

from extensions import db
from models.api_token import ApiToken


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_api_token(user_id: int, name: str, expires_days: int | None = None):
    if not name.strip() or len(name.strip()) > 100 or (expires_days is not None and not 1 <= expires_days <= 365):
        raise ValueError("Invalid token name or lifetime")
    raw = f"se2026_{secrets.token_urlsafe(36)}"
    token = ApiToken(
        user_id=user_id,
        name=name.strip(),
        token_prefix=raw[:12],
        token_hash=_hash_token(raw),
        expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
    )
    db.session.add(token)
    db.session.commit()
    return token, raw


def authenticate_bearer_token(raw_token: str):
    if not raw_token:
        return None
    token = ApiToken.query.filter_by(token_hash=_hash_token(raw_token), is_active=True).first()
    if not token or (token.expires_at and token.expires_at < datetime.utcnow()):
        return None
    if not token.user or not token.user.is_active or token.user.role != "admin":
        return None
    token.last_used_at = datetime.utcnow()
    db.session.commit()
    return token

