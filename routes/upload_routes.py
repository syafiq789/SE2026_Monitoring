from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from extensions import db
from models.upload_history import UploadHistory
from services.upload_service import import_prepared_data, prepare_import_data
from utils.decorators import admin_required
from utils.validators import ImportValidationError, ensure_allowed_file


upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload")
@admin_required
def upload():
    return render_template("upload.html")


def _record_failure(file_info, message):
    history = UploadHistory(
        user_id=session.get("user_id"),
        original_filename=file_info.get("original", "-"),
        stored_filename=file_info.get("stored", "-"),
        processed_sheet=file_info.get("sheet"),
        file_type=file_info.get("extension", "-"),
        file_size=file_info.get("size", 0),
        status="failed",
        message=str(message)[:65000],
    )
    db.session.add(history)
    db.session.commit()


@upload_bp.route("/upload-data", methods=["POST"])
@admin_required
def upload_data():
    incoming = request.files.get("file")
    if not incoming or not incoming.filename:
        flash("Pilih file XLSX atau CSV terlebih dahulu.", "danger")
        return redirect(url_for("upload.upload"))

    file_info = {"original": incoming.filename, "stored": "-", "size": 0, "extension": "-"}
    try:
        extension = ensure_allowed_file(incoming.filename)
        safe_name = secure_filename(incoming.filename) or f"data_sls.{extension}"
        stored_name = f"{uuid4().hex}_{safe_name}"
        destination = Path(current_app.config["UPLOAD_FOLDER"]) / stored_name
        incoming.save(destination)
        file_info.update(
            {"stored": stored_name, "size": destination.stat().st_size, "extension": extension}
        )

        prepared = prepare_import_data(destination)
        file_info["sheet"] = prepared["processed_sheet"]
        summary = import_prepared_data(prepared)
        history = UploadHistory(
            user_id=session["user_id"],
            original_filename=incoming.filename,
            stored_filename=stored_name,
            processed_sheet=prepared["processed_sheet"],
            file_type=extension,
            file_size=file_info["size"],
            source_rows=prepared["source_rows"],
            imported_rows=summary["total_sls"],
            skipped_rows=prepared["skipped_rows"],
            duplicate_rows=prepared["duplicate_rows"],
            warning_count=len(prepared["warnings"]),
            **summary,
            status="success",
            message=("; ".join(prepared["warnings"][:100]) or "Import berhasil tanpa peringatan."),
        )
        db.session.add(history)
        db.session.commit()
        flash(
            f"Import berhasil: {summary['total_sls']:,} SLS, {summary['total_target']:,} target, "
            f"progress {summary['progress']:.2f}%.",
            "success",
        )
        if prepared["warnings"]:
            flash(f"Import selesai dengan {len(prepared['warnings'])} peringatan validasi.", "warning")
        return redirect(url_for("dashboard.dashboard"))
    except ImportValidationError as exc:
        db.session.rollback()
        detail = str(exc)
        if exc.read_columns:
            detail += f" Kolom yang berhasil dibaca: {', '.join(exc.read_columns)}."
        if exc.missing_columns:
            detail += f" Kolom yang belum ditemukan: {', '.join(exc.missing_columns)}."
        try:
            _record_failure(file_info, detail)
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Gagal menyimpan riwayat upload gagal")
        flash(detail, "danger")
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Import SLS gagal")
        try:
            _record_failure(file_info, f"Gagal insert database: {exc}")
        except Exception:
            db.session.rollback()
        flash("Import gagal. Data monitoring lama tetap tersedia. Periksa format file dan log aplikasi.", "danger")
    return redirect(url_for("upload.upload"))


@upload_bp.route("/riwayat-upload")
@admin_required
def upload_history():
    histories = UploadHistory.query.order_by(UploadHistory.uploaded_at.desc()).all()
    return render_template("upload_history.html", histories=histories)

