from pathlib import Path

import pandas as pd
from flask import current_app
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from services.monitoring_service import get_kecamatan_rows, get_pcl_rows, get_pml_rows, get_sls_rows
from utils.helpers import export_timestamp, local_now


EXPORT_COLUMNS = {
    "sls": [
        ("kec_code", "Kode Kecamatan"), ("kec_name", "Nama Kecamatan"),
        ("desa_code", "Kode Desa"), ("desa_name", "Nama Desa"),
        ("subsls_code", "ID Sub-SLS"), ("subsls_name", "Nama Sub-SLS"),
        ("nama_pml", "Nama PML"), ("nama_pcl", "Nama PCL"),
        ("total_target", "Total Target"), ("open_count", "Open"),
        ("draft_count", "Draft"), ("processed_count", "Sudah Upload"),
        ("remaining_count", "Belum Upload"), ("approved_by_pengawas", "Approved"),
        ("progress", "Progress (%)"), ("progress_status", "Status"),
        ("completed_by_admin_kabupaten", "Completed Admin Kabupaten"),
        ("edited_by_admin_kabupaten", "Edited Admin Kabupaten"),
        ("edited_by_pengawas", "Edited Pengawas"),
        ("rejected_by_admin_kabupaten", "Rejected Admin Kabupaten"),
        ("rejected_by_pengawas", "Rejected Pengawas"),
        ("revoked_by_admin_kabupaten", "Revoked Admin Kabupaten"),
        ("revoked_by_pengawas", "Revoked Pengawas"),
        ("submitted_by_pencacah", "Submitted Pencacah"),
        ("submitted_respondent", "Submitted Respondent"),
    ],
    "pcl": [
        ("kec_code", "Kode Kecamatan"), ("kec_name", "Nama Kecamatan"),
        ("nama_pml", "Nama PML"), ("nama_pcl", "Nama PCL"),
        ("jumlah_sls", "Jumlah SLS"), ("total_target", "Total Target"),
        ("open_count", "Open"), ("draft_count", "Draft"),
        ("processed_count", "Sudah Upload"), ("remaining_count", "Belum Upload"),
        ("approved_count", "Approved"), ("progress", "Progress (%)"),
    ],
    "pml": [
        ("kec_code", "Kode Kecamatan"), ("kec_name", "Nama Kecamatan"),
        ("nama_pml", "Nama PML"), ("jumlah_pcl", "Jumlah PCL"),
        ("jumlah_sls", "Jumlah SLS"), ("total_target", "Total Target"),
        ("open_count", "Open"), ("draft_count", "Draft"),
        ("processed_count", "Sudah Upload"), ("remaining_count", "Belum Upload"),
        ("approved_count", "Approved"), ("progress", "Progress (%)"),
    ],
    "kecamatan": [
        ("kec_code", "Kode Kecamatan"), ("kec_name", "Nama Kecamatan"),
        ("jumlah_pml", "Jumlah PML"), ("jumlah_pcl", "Jumlah PCL"),
        ("jumlah_sls", "Jumlah SLS"), ("total_target", "Total Target"),
        ("open_count", "Open"), ("draft_count", "Draft"),
        ("processed_count", "Sudah Upload"), ("remaining_count", "Belum Upload"),
        ("approved_count", "Approved"), ("progress", "Progress (%)"),
    ],
}


def _rows(level, filters):
    return {
        "sls": get_sls_rows,
        "pcl": get_pcl_rows,
        "pml": get_pml_rows,
        "kecamatan": get_kecamatan_rows,
    }[level](filters)


def _dataframe(level, filters):
    rows = _rows(level, filters)
    columns = EXPORT_COLUMNS[level]
    data = [{label: row.get(key, "") for key, label in columns} for row in rows]
    return pd.DataFrame(data, columns=[label for _, label in columns])


def create_export(level: str, file_type: str, filters: dict) -> Path:
    if level not in EXPORT_COLUMNS or file_type not in {"csv", "excel"}:
        raise ValueError("Jenis export tidak dikenal.")
    frame = _dataframe(level, filters)
    output_dir = Path(current_app.config["EXPORT_FOLDER"])
    output_dir.mkdir(parents=True, exist_ok=True)
    extension = "xlsx" if file_type == "excel" else "csv"
    path = output_dir / f"monitoring_{level}_{export_timestamp()}.{extension}"

    if file_type == "csv":
        frame.to_csv(path, index=False, encoding="utf-8-sig")
        return path

    sheet_name = f"Monitoring {level.upper()}"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=sheet_name, startrow=3)
        worksheet = writer.book[sheet_name]
        worksheet["A1"] = f"MONITORING {level.upper()} - SENSUS EKONOMI 2026"
        worksheet["A2"] = "BPS Kabupaten Banyuwangi"
        worksheet["A3"] = f"Tanggal export: {local_now().strftime('%d-%m-%Y %H:%M:%S')}"
        worksheet["A1"].font = Font(bold=True, size=14, color="7A3E12")
        worksheet["A2"].font = Font(bold=True, color="C65D16")
        header_fill = PatternFill("solid", fgColor="7A3E12")
        for cell in worksheet[4]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        worksheet.freeze_panes = "A5"
        last_column = get_column_letter(max(worksheet.max_column, 1))
        worksheet.auto_filter.ref = f"A4:{last_column}{max(worksheet.max_row, 4)}"
        for index, column in enumerate(frame.columns, start=1):
            values = [len(str(column))] + [len(str(value)) for value in frame[column].head(1000)]
            worksheet.column_dimensions[get_column_letter(index)].width = min(max(values) + 2, 45)
            if "Progress" in str(column):
                for cell in worksheet[get_column_letter(index)][4:]:
                    cell.number_format = '0.00"%"'
    return path
