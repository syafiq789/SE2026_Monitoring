from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.user import User
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


