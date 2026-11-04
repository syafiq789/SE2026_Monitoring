import logging
import os

from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import OperationalError

from config import Config
from extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["EXPORT_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    from routes.api_routes import api_bp
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.export_routes import export_bp
    from routes.followup_routes import followup_bp
    from routes.gis_routes import gis_bp
    from routes.log_routes import log_bp
    from routes.monitoring_routes import monitoring_bp
    from routes.upload_routes import upload_bp
    from routes.user_routes import user_bp

    for blueprint in (
        auth_bp,
        dashboard_bp,
        monitoring_bp,
        gis_bp,
        followup_bp,
        upload_bp,
        export_bp,
        user_bp,
        log_bp,
        api_bp,
    ):
        app.register_blueprint(blueprint)

    _tables_initialized = False

    @app.before_request
    def ensure_extra_tables():
        nonlocal _tables_initialized
        if os.getenv("VERCEL"):
            from config import ensure_vercel_sqlite_seeded

            ensure_vercel_sqlite_seeded()
        if not _tables_initialized:
            try:
                import models.activity_log
                from models.user import User

                db.create_all()
                if User.query.count() == 0:
                    admin_user = User(
                        nama_lengkap="Administrator",
                        username="admin",
                        email="admin@se2026.local",
                        role="admin",
                        is_active=True,
                    )
                    admin_user.set_password("admin123")
                    reg_user = User(
                        nama_lengkap="Pengguna Monitoring",
                        username="user",
                        email="user@se2026.local",
                        role="user",
                        is_active=True,
                    )
                    reg_user.set_password("user123")
                    db.session.add_all([admin_user, reg_user])
                    db.session.commit()
                _tables_initialized = True
            except Exception:
                db.session.rollback()
        from routes.auth_routes import _sync_registered_snapshots

        _sync_registered_snapshots()

    @app.route("/")
    def index():
        from utils.decorators import _current_user

        user = _current_user()
        if user and user.is_active:
            return redirect(url_for("dashboard.dashboard"))
        session.clear()
        return redirect(url_for("auth.login"))

    @app.context_processor
    def inject_globals():
        from utils.decorators import _current_user

        return {"current_user": _current_user()}

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(_error):
        flash("Ukuran file melebihi batas maksimum 32 MB.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    @app.errorhandler(OperationalError)
    def database_unavailable(error):
        db.session.rollback()
        app.logger.exception("Database tidak tersedia: %s", error)
        return render_template(
            "500.html",
            friendly_message="Tidak dapat terhubung ke database. Pastikan MySQL Laragon sudah dijalankan.",
        ), 500

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.exception("Kesalahan aplikasi: %s", error)
        return render_template("500.html", friendly_message=None), 500

    try:
        log_dir = Path("/tmp") if os.getenv("VERCEL") else Path(app.root_path)
        log_file = log_dir / "se2026.log"
        handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        handler.setLevel(logging.INFO)
        if not any(isinstance(item, RotatingFileHandler) for item in app.logger.handlers):
            app.logger.addHandler(handler)
    except OSError:
        pass

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config.get("DEBUG", False))
