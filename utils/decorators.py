from functools import wraps

from flask import abort, flash, redirect, request, session, url_for

from extensions import db
from models.user import User


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    try:
        user = db.session.get(User, user_id)
    except Exception:
        db.session.rollback()
        user = None

    if not user and session.get("user_snapshot"):
        snap = session["user_snapshot"]
        try:
            user = User.query.filter(
                (User.username == snap.get("username")) | (User.email == snap.get("email"))
            ).first()
            if not user:
                user = User(
                    id=snap.get("id", user_id),
                    nama_lengkap=snap.get("nama_lengkap", "Pengguna"),
                    username=snap.get("username", f"user_{user_id}"),
                    email=snap.get("email", f"user_{user_id}@se2026.local"),
                    password_hash=snap.get("password_hash", ""),
                    role=snap.get("role", "user"),
                    is_active=bool(snap.get("is_active", True)),
                )
                db.session.add(user)
                db.session.commit()
            session["user_id"] = user.id
        except Exception:
            db.session.rollback()

    return user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _current_user()
        if not user or not user.is_active:
            session.clear()
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = _current_user()
        if not user or not user.is_active:
            session.clear()
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        if user.role != "admin":
            flash("Akses ditolak. Fitur ini hanya bisa diakses oleh Admin.", "danger")
            abort(403)
        return view(*args, **kwargs)

    return wrapped
