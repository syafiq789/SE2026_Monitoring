from io import BytesIO
from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from werkzeug.utils import secure_filename

from extensions import db
from models.upload_history import UploadHistory
from services.activity_service import log_activity
from services.upload_service import import_prepared_data, prepare_import_data
from utils.decorators import admin_required
from utils.validators import ImportValidationError, ensure_allowed_file


upload_bp = Blueprint("upload", __name__)


# =========================================================
# TEMPLATE NAMA KOLOM FILE SLS
# =========================================================
#
# Daftar berikut adalah susunan header/template file XLSX atau CSV
# yang ditampilkan pada halaman upload dan digunakan saat pengguna
# mengunduh template Excel.
#
# Nama kolom harus tetap sama. Urutan kolom pada file yang diunggah
# boleh berbeda selama mapper di upload_service mendukungnya.
# =========================================================

TEMPLATE_COLUMNS = [
    {
        "column": "prov",
        "description": "Kode provinsi 2 digit. Simpan sebagai teks.",
        "example": "35",
    },
    {
        "column": "kab",
        "description": "Kode kabupaten 2 digit. Simpan sebagai teks.",
        "example": "10",
    },
    {
        "column": "kec_code",
        "description": "Kode kecamatan 3 digit. Nol di depan harus dipertahankan.",
        "example": "010",
    },
    {
        "column": "kec_name",
        "description": "Nama kecamatan.",
        "example": "Pesanggaran",
    },
    {
        "column": "desa_code",
        "description": "Kode desa atau kelurahan 3 digit.",
        "example": "001",
    },
    {
        "column": "desa_name",
        "description": "Nama desa atau kelurahan.",
        "example": "Sumberagung",
    },
    {
        "column": "subsls_code",
        "description": "Kode Sub-SLS 6 digit. Simpan sebagai teks.",
        "example": "000001",
    },
    {
        "column": "subsls_name",
        "description": "Nama atau nomor Sub-SLS.",
        "example": "SLS 001",
    },
    {
        "column": "email",
        "description": "Alamat email PCL.",
        "example": "pcl@example.com",
    },
    {
        "column": "username",
        "description": "Username PCL pada sistem pendataan.",
        "example": "pcl001",
    },
    {
        "column": "APPROVED.BY.Pengawas",
        "description": "Jumlah data yang disetujui pengawas.",
        "example": "50",
    },
    {
        "column": "COMPLETED.BY.Admin.Kabupaten",
        "description": "Jumlah data yang diselesaikan Admin Kabupaten.",
        "example": "5",
    },
    {
        "column": "DRAFT",
        "description": "Jumlah data berstatus DRAFT.",
        "example": "10",
    },
    {
        "column": "EDITED.BY.Admin.Kabupaten",
        "description": "Jumlah data yang diedit Admin Kabupaten.",
        "example": "0",
    },
    {
        "column": "EDITED.BY.Pengawas",
        "description": "Jumlah data yang diedit pengawas.",
        "example": "2",
    },
    {
        "column": "OPEN",
        "description": "Jumlah data berstatus OPEN.",
        "example": "20",
    },
    {
        "column": "REJECTED.BY.Admin.Kabupaten",
        "description": "Jumlah data yang ditolak Admin Kabupaten.",
        "example": "0",
    },
    {
        "column": "REJECTED.BY.Pengawas",
        "description": "Jumlah data yang ditolak pengawas.",
        "example": "1",
    },
    {
        "column": "REVOKED.BY.Admin.Kabupaten",
        "description": "Jumlah data yang ditarik kembali Admin Kabupaten.",
        "example": "0",
    },
    {
        "column": "REVOKED.BY.Pengawas",
        "description": "Jumlah data yang ditarik kembali pengawas.",
        "example": "0",
    },
    {
        "column": "SUBMITTED.BY.Pencacah",
        "description": "Jumlah data yang dikirim oleh pencacah.",
        "example": "40",
    },
    {
        "column": "SUBMITTED.RESPONDENT",
        "description": "Jumlah data yang dikirim oleh responden.",
        "example": "7",
    },
    {
        "column": "total",
        "description": "Jumlah seluruh target pada Sub-SLS.",
        "example": "120",
    },
    {
        "column": "email PML",
        "description": "Alamat email PML.",
        "example": "pml@example.com",
    },
    {
        "column": "PCL",
        "description": "Nama Petugas Pencacah Lapangan.",
        "example": "Ahmad Fauzi",
    },
    {
        "column": "PML",
        "description": "Nama Petugas Pemeriksa Lapangan.",
        "example": "Siti Aminah",
    },
]

TEMPLATE_NOTES = [
    "File yang diperbolehkan adalah XLSX dan CSV.",
    "Untuk file Excel, gunakan sheet bernama sls.",
    "Baris pertama file harus berisi nama kolom/template.",
    "Nama kolom harus sama seperti template, tetapi urutannya boleh berbeda.",
    "Jangan menggunakan merge cell pada header maupun isi data.",
    (
        "Kolom prov, kab, kec_code, desa_code, dan subsls_code "
        "sebaiknya menggunakan format Text."
    ),
    "Angka nol di depan kode wilayah tidak boleh dihilangkan.",
    (
        "Kolom total, OPEN, DRAFT, dan kolom jumlah status lainnya "
        "harus berupa angka bulat dan tidak boleh negatif."
    ),
    "Satu baris data mewakili satu Sub-SLS.",
    (
        "Cukup unggah satu file SLS. Monitoring Kecamatan, PML, dan PCL "
        "akan diperbarui secara otomatis."
    ),
]


# =========================================================
# HALAMAN UPLOAD
# =========================================================

@upload_bp.route("/upload")
@admin_required
def upload():
    max_content_length = current_app.config.get(
        "MAX_CONTENT_LENGTH",
        32 * 1024 * 1024,
    )

    if not max_content_length:
        max_content_length = 32 * 1024 * 1024

    max_file_size_mb = round(
        max_content_length / (1024 * 1024)
    )

    return render_template(
        "upload.html",
        # Variabel utama untuk daftar template nama kolom.
        template_columns=TEMPLATE_COLUMNS,
        template_notes=TEMPLATE_NOTES,
        max_file_size_mb=max_file_size_mb,

        # Tetap dikirim agar kompatibel jika upload.html lama masih
        # menggunakan required_template_columns/optional_template_columns.
        required_template_columns=TEMPLATE_COLUMNS,
        optional_template_columns=[],
    )


# =========================================================
# DOWNLOAD TEMPLATE EXCEL
# =========================================================

@upload_bp.route("/download-template")
@admin_required
def download_template():
    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "sls"

    headers = [
        item["column"]
        for item in TEMPLATE_COLUMNS
    ]

    # Sheet sls hanya berisi header agar baris contoh tidak ikut
    # terimpor sebagai data asli.
    worksheet.append(headers)

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="7C2D12",
    )

    header_font = Font(
        color="FFFFFF",
        bold=True,
    )

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    text_columns = {
        "prov",
        "kab",
        "kec_code",
        "desa_code",
        "subsls_code",
    }

    for column_index, header in enumerate(
        headers,
        start=1,
    ):
        column_letter = get_column_letter(column_index)

        worksheet.column_dimensions[column_letter].width = max(
            14,
            min(len(header) + 5, 38),
        )

        if header in text_columns:
            # Menyiapkan format kolom untuk baris data setelah header.
            for row_number in range(2, 1002):
                worksheet.cell(
                    row=row_number,
                    column=column_index,
                ).number_format = "@"

    # Sheet keterangan nama kolom.
    information_sheet = workbook.create_sheet("Keterangan")

    information_sheet.append(
        [
            "No.",
            "Nama Kolom",
            "Keterangan",
            "Contoh Isi",
        ]
    )

    for cell in information_sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    for index, item in enumerate(TEMPLATE_COLUMNS, start=1):
        information_sheet.append(
            [
                index,
                item["column"],
                item["description"],
                item["example"],
            ]
        )

    information_sheet.column_dimensions["A"].width = 8
    information_sheet.column_dimensions["B"].width = 38
    information_sheet.column_dimensions["C"].width = 75
    information_sheet.column_dimensions["D"].width = 28

    for row in information_sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

    # Sheet ketentuan upload.
    notes_sheet = workbook.create_sheet("Ketentuan Upload")

    notes_sheet.append(
        [
            "No.",
            "Ketentuan",
        ]
    )

    for cell in notes_sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    for index, note in enumerate(TEMPLATE_NOTES, start=1):
        notes_sheet.append(
            [
                index,
                note,
            ]
        )

    notes_sheet.column_dimensions["A"].width = 10
    notes_sheet.column_dimensions["B"].width = 100

    for row in notes_sheet.iter_rows(min_row=2):
        row[1].alignment = Alignment(
            vertical="top",
            wrap_text=True,
        )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="template_data_sls_se2026.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


# =========================================================
# MENYIMPAN RIWAYAT UPLOAD GAGAL
# =========================================================

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


# =========================================================
# PROSES UPLOAD DAN IMPORT DATA
# =========================================================

@upload_bp.route(
    "/upload-data",
    methods=["POST"],
)
@admin_required
def upload_data():
    incoming = request.files.get("file")

    if not incoming or not incoming.filename:
        flash(
            "Pilih file XLSX atau CSV terlebih dahulu.",
            "danger",
        )

        return redirect(
            url_for("upload.upload")
        )

    file_info = {
        "original": incoming.filename,
        "stored": "-",
        "size": 0,
        "extension": "-",
        "sheet": None,
    }

    try:
        extension = ensure_allowed_file(
            incoming.filename
        )

        safe_name = (
            secure_filename(incoming.filename)
            or f"data_sls.{extension}"
        )

        stored_name = f"{uuid4().hex}_{safe_name}"

        upload_folder = Path(
            current_app.config["UPLOAD_FOLDER"]
        )

        upload_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = upload_folder / stored_name
        incoming.save(destination)

        file_info.update(
            {
                "stored": stored_name,
                "size": destination.stat().st_size,
                "extension": extension,
            }
        )

        prepared = prepare_import_data(destination)

        file_info["sheet"] = prepared[
            "processed_sheet"
        ]

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
            message=(
                "; ".join(prepared["warnings"][:100])
                or "Import berhasil tanpa peringatan."
            ),
        )

        db.session.add(history)
        db.session.commit()

        log_activity(
            user_id=session.get("user_id"),
            action="UPLOAD",
            target=file_info.get("original", "Data SLS"),
            details=f"Import berhasil: {summary['total_sls']:,} SLS, {summary['total_target']:,} target, progress {summary['progress']:.2f}%",
            ip_address=request.remote_addr,
        )

        flash(
            (
                f"Import berhasil: "
                f"{summary['total_sls']:,} SLS, "
                f"{summary['total_target']:,} target, "
                f"progress {summary['progress']:.2f}%."
            ),
            "success",
        )

        if prepared["warnings"]:
            flash(
                (
                    "Import selesai dengan "
                    f"{len(prepared['warnings'])} "
                    "peringatan validasi."
                ),
                "warning",
            )

        return redirect(
            url_for("dashboard.dashboard")
        )

    except ImportValidationError as exc:
        db.session.rollback()

        detail = str(exc)

        if getattr(exc, "read_columns", None):
            detail += (
                " Kolom yang berhasil dibaca: "
                f"{', '.join(exc.read_columns)}."
            )

        if getattr(exc, "missing_columns", None):
            detail += (
                " Kolom yang belum ditemukan: "
                f"{', '.join(exc.missing_columns)}."
            )

        try:
            _record_failure(
                file_info,
                detail,
            )

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                "Gagal menyimpan riwayat upload gagal"
            )

        flash(
            detail,
            "danger",
        )

    except Exception as exc:
        db.session.rollback()

        current_app.logger.exception(
            "Import SLS gagal"
        )

        try:
            _record_failure(
                file_info,
                f"Gagal insert database: {exc}",
            )

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                "Gagal menyimpan detail kegagalan import"
            )

        flash(
            (
                "Import gagal. Data monitoring lama tetap tersedia. "
                "Periksa format file dan log aplikasi."
            ),
            "danger",
        )

    return redirect(
        url_for("upload.upload")
    )


# =========================================================
# RIWAYAT UPLOAD
# =========================================================

@upload_bp.route("/riwayat-upload")
@admin_required
def upload_history():
    histories = UploadHistory.query.order_by(
        UploadHistory.uploaded_at.desc()
    ).all()

    return render_template(
        "upload_history.html",
        histories=histories,
    )