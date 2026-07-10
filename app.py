import logging
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
    from routes.monitoring_routes import monitoring_bp
    from routes.upload_routes import upload_bp
    from routes.user_routes import user_bp

    for blueprint in (
        auth_bp,
        dashboard_bp,
        monitoring_bp,
        upload_bp,
        export_bp,
        user_bp,
        api_bp,
    ):
        app.register_blueprint(blueprint)

    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("auth.login"))

    @app.context_processor
    def inject_globals():
        from models.user import User

        current_user = None
        if session.get("user_id"):
            try:
                current_user = db.session.get(User, session["user_id"])
            except Exception:
                db.session.rollback()
        return {"current_user": current_user}

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

    log_file = Path(app.root_path) / "se2026.log"
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    handler.setLevel(logging.INFO)
    if not any(isinstance(item, RotatingFileHandler) for item in app.logger.handlers):
        app.logger.addHandler(handler)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config.get("DEBUG", False))

