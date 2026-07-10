from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.api_token import ApiToken
from models.user import User
from services.token_service import create_api_token
from utils.decorators import admin_required


user_bp = Blueprint("users", __name__)


@user_bp.route("/admin/users")
@admin_required
def users():
    return render_template("users.html", users=User.query.order_by(User.created_at.desc()).all())


@user_bp.route("/admin/register", methods=["GET", "POST"])
@admin_required
def admin_register():
    if request.method == "POST":
        nama = request.form.get("nama_lengkap", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "user")
        password = request.form.get("password", "")
        if role not in {"admin", "user"} or not all([nama, username, email, password]):
            flash("Data pengguna tidak lengkap atau role tidak valid.", "danger")
        elif len(password) < 8:
            flash("Password minimal 8 karakter.", "danger")
        else:
            user = User(nama_lengkap=nama, username=username, email=email, role=role, is_active=True)
            user.set_password(password)
            try:
                db.session.add(user)
                db.session.commit()
                flash("Pengguna berhasil dibuat.", "success")
                return redirect(url_for("users.users"))
            except IntegrityError:
                db.session.rollback()
                flash("Username atau email sudah digunakan.", "danger")
    return render_template("admin_register.html")


@user_bp.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == session.get("user_id") and user.is_active:
        flash("Anda tidak dapat menonaktifkan akun sendiri.", "warning")
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash("Status pengguna diperbarui.", "success")
    return redirect(url_for("users.users"))


@user_bp.route("/api/tokens")
@admin_required
def api_tokens():
    tokens = ApiToken.query.order_by(ApiToken.created_at.desc()).all()
    return render_template("api_tokens.html", tokens=tokens, new_token=None)


@user_bp.route("/api/tokens/create", methods=["POST"])
@admin_required
def api_token_create():
    name = request.form.get("name", "").strip()
    expires_days = request.form.get("expires_days", type=int)
    if not name:
        flash("Nama token wajib diisi.", "danger")
        return redirect(url_for("users.api_tokens"))
    _token, raw = create_api_token(session["user_id"], name, expires_days if expires_days and expires_days > 0 else None)
    tokens = ApiToken.query.order_by(ApiToken.created_at.desc()).all()
    flash("Token dibuat. Salin sekarang karena token tidak akan ditampilkan lagi.", "success")
    return render_template("api_tokens.html", tokens=tokens, new_token=raw)


@user_bp.route("/api/tokens/<int:token_id>/revoke", methods=["POST"])
@admin_required
def api_token_revoke(token_id):
    token = db.get_or_404(ApiToken, token_id)
    token.is_active = False
    db.session.commit()
    flash("Token dinonaktifkan.", "success")
    return redirect(url_for("users.api_tokens"))

