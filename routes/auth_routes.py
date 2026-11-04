from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.user import User
from services.activity_service import log_activity
from utils.decorators import login_required


auth_bp = Blueprint("auth", __name__)


def _safe_next(value):
    if value and not urlparse(value).netloc and value.startswith("/"):
        return value
    return url_for("dashboard.dashboard")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "1"

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user or not user.check_password(password):
            log_activity(
                action="LOGIN_FAILED",
                target=username,
                details="Percobaan login gagal: kredensial tidak valid",
                ip_address=request.remote_addr,
            )
            flash("Username, email, atau password salah. Pastikan Anda sudah mendaftarkan akun.", "danger")
            return render_template("login.html")

        if not user.is_active:
            flash("Akun Anda sedang dinonaktifkan.", "warning")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user.id
        session.permanent = remember

        log_activity(
            user_id=user.id,
            action="LOGIN",
            target=user.username,
            details=f"User {user.username} ({user.role}) berhasil login",
            ip_address=request.remote_addr,
        )

        next_url = request.form.get("next") or request.args.get("next")
        return redirect(_safe_next(next_url))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nama = request.form.get("nama_lengkap", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "user").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if role not in {"admin", "user"}:
            role = "user"

        if not all([nama, username, email, password]):
            flash("Semua kolom wajib diisi.", "danger")
        elif len(password) < 8:
            flash("Password minimal 8 karakter.", "danger")
        elif password != confirm:
            flash("Konfirmasi password tidak sama.", "danger")
        else:
            user = User(
                nama_lengkap=nama,
                username=username,
                email=email,
                role=role,
                is_active=True,
            )
            user.set_password(password)
            try:
                db.session.add(user)
                db.session.commit()
                log_activity(
                    user_id=user.id,
                    action="REGISTER",
                    target=username,
                    details=f"Pendaftaran akun baru ({role.upper()}): {nama} ({email})",
                    ip_address=request.remote_addr,
                )
                flash(
                    f"Registrasi akun {role.upper()} berhasil! Silakan login untuk mengakses sistem.",
                    "success",
                )
                return redirect(url_for("auth.login"))
            except IntegrityError:
                db.session.rollback()
                flash("Username atau email sudah digunakan. Silakan gunakan yang lain.", "danger")

    return render_template("login.html", active_tab="register")


@auth_bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    uid = session.get("user_id")
    log_activity(
        user_id=uid,
        action="LOGOUT",
        target=str(uid),
        details="User logout dari sesi",
        ip_address=request.remote_addr,
    )
    session.clear()
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))
