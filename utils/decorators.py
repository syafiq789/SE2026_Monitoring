from functools import wraps

from flask import abort, flash, redirect, request, session, url_for

from extensions import db
from models.user import User


def _current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


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


