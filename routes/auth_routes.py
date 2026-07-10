from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.user import User
from services.auth_service import authenticate
from utils.decorators import login_required


auth_bp = Blueprint("auth", __name__)


def _safe_next(value):
    if value and not urlparse(value).netloc and value.startswith("/"):
        return value
    return url_for("dashboard.dashboard")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard.dashboard"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        user = authenticate(identity, password)
        if user:
            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            flash(f"Selamat datang, {user.nama_lengkap}.", "success")
            return redirect(_safe_next(request.args.get("next")))
        flash("Username/email atau password tidak sesuai, atau akun tidak aktif.", "danger")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nama = request.form.get("nama_lengkap", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not all([nama, username, email, password]):
            flash("Semua kolom wajib diisi.", "danger")
        elif len(password) < 8:
            flash("Password minimal 8 karakter.", "danger")
        elif password != confirm:
            flash("Konfirmasi password tidak sama.", "danger")
        else:
            user = User(nama_lengkap=nama, username=username, email=email, role="user", is_active=True)
            user.set_password(password)
            try:
                db.session.add(user)
                db.session.commit()
                flash("Registrasi berhasil. Silakan login.", "success")
                return redirect(url_for("auth.login"))
            except IntegrityError:
                db.session.rollback()
                flash("Username atau email sudah digunakan.", "danger")
    return render_template("register.html")


@auth_bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    session.clear()
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))

