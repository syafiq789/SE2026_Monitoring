from datetime import datetime

from extensions import db


class ApiToken(db.Model):
    __tablename__ = "api_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False)
    token_prefix = db.Column(db.String(16), nullable=False, index=True)
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    expires_at = db.Column(db.DateTime)
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("api_tokens", cascade="all, delete-orphan"))

