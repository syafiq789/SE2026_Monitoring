from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, session, url_for

from services.activity_service import log_activity
from services.export_service import create_export
from utils.decorators import admin_required
from utils.helpers import filters_from_request


export_bp = Blueprint("export", __name__)


@export_bp.route("/download")
@admin_required
def download():
    return render_template("download.html")


def _export(level, file_type):
    try:
        path = create_export(level, file_type, filters_from_request(request.args))
        log_activity(
            user_id=session.get("user_id"),
            action="EXPORT",
            target=f"{level.upper()}_{file_type.upper()}",
            details=f"Unduh file: {path.name}",
            ip_address=request.remote_addr,
        )
        mimetype = (
            "text/csv; charset=utf-8"
            if file_type == "csv"
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        return send_file(path, as_attachment=True, download_name=path.name, mimetype=mimetype)
    except Exception as exc:
        current_app.logger.exception("Gagal membuat export %s %s: %s", level, file_type, exc)
        flash("Gagal membuat export. Silakan periksa log aplikasi.", "danger")
        return redirect(url_for("export.download"))


for _level in ("sls", "pcl", "pml", "kecamatan"):
    for _type in ("csv", "excel"):
        export_bp.add_url_rule(
            f"/export/{_level}/{_type}",
            endpoint=f"export_{_level}_{_type}",
            view_func=admin_required(lambda level=_level, file_type=_type: _export(level, file_type)),
        )
