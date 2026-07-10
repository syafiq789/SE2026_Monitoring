from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, insert

from extensions import db
from models.monitoring import Kecamatan, PCL, PML, SLS
from utils.calculations import aggregate_progress, calculate_progress
from utils.column_mapper import (
    DETAIL_STATUS_COLUMNS,
    NUMERIC_COLUMNS,
    REQUIRED_COLUMNS,
    normalize_dataframe_columns,
)
from utils.validators import ImportValidationError, clean_code, clean_text


WORKFLOW_COLUMNS = [
    "approved_by_pengawas",
    "completed_by_admin_kabupaten",
    "draft_count",
    "edited_by_admin_kabupaten",
    "edited_by_pengawas",
    "open_count",
    "rejected_by_admin_kabupaten",
    "rejected_by_pengawas",
    "revoked_by_admin_kabupaten",
    "revoked_by_pengawas",
    "submitted_by_pencacah",
    "submitted_respondent",
]

SHEET_SIGNATURE_COLUMNS = {
    "kec_code", "kec_name", "subsls_code", "subsls_name",
    "nama_pcl", "nama_pml", "total_target", "open_count", "draft_count",
}

IDENTITY_COLUMNS = [
    "prov",
    "kab",
    "kec_code",
    "kec_name",
    "desa_code",
    "desa_name",
    "subsls_code",
    "subsls_name",
    "email_pcl",
    "username_pcl",
    "email_pml",
    "nama_pcl",
    "nama_pml",
]


def _drop_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep = []
    for column in df.columns:
        normalized = str(column).strip().lower()
        if normalized.startswith("unnamed:"):
            continue
        if df[column].isna().all():
            continue
        keep.append(column)
    return df.loc[:, keep]


def _sheet_has_sls_columns(excel: pd.ExcelFile, sheet_name: str) -> bool:
    try:
        header = pd.read_excel(excel, sheet_name=sheet_name, nrows=0)
        columns = set(normalize_dataframe_columns(header).columns)
        return SHEET_SIGNATURE_COLUMNS.issubset(columns)
    except Exception:
        return False


def read_sls_source(file_path: str | Path) -> tuple[pd.DataFrame, str]:
    path = Path(file_path)
    extension = path.suffix.lower()
    try:
        if extension == ".csv":
            try:
                frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
            except UnicodeDecodeError:
                frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="latin-1")
            return frame, "CSV"
        if extension != ".xlsx":
            raise ImportValidationError("Format file tidak didukung. Gunakan file XLSX atau CSV.")

        excel = pd.ExcelFile(path, engine="openpyxl")
        selected = next((name for name in excel.sheet_names if name.strip().lower() == "sls"), None)
        if not selected:
            selected = next((name for name in excel.sheet_names if _sheet_has_sls_columns(excel, name)), None)
        if not selected:
            raise ImportValidationError(
                'Sheet SLS tidak ditemukan. Pastikan file Excel memiliki sheet bernama "sls".'
            )
        frame = pd.read_excel(
            excel,
            sheet_name=selected,
            dtype=str,
            keep_default_na=False,
        )
        return frame, selected
    except ImportValidationError:
        raise
    except Exception as exc:
        raise ImportValidationError(f"Excel tidak dapat dibaca atau file rusak: {exc}") from exc


def _convert_numeric(series: pd.Series, column: str, warnings: list[str]) -> pd.Series:
    cleaned = series.astype(str).str.strip().replace({"": None, "nan": None, "None": None})
    numeric = pd.to_numeric(cleaned, errors="coerce")
    invalid_mask = cleaned.notna() & numeric.isna()
    for index in series.index[invalid_mask][:50]:
        warnings.append(f"Nilai numerik tidak valid pada baris {index + 2}, kolom {column}; diubah menjadi 0.")
    negative_mask = numeric.fillna(0) < 0
    for index in series.index[negative_mask][:50]:
        warnings.append(f"Nilai negatif pada baris {index + 2}, kolom {column}; diubah menjadi 0.")
    return numeric.fillna(0).clip(lower=0).round().astype("int64")


def prepare_import_data(file_path: str | Path) -> dict:
    raw, processed_sheet = read_sls_source(file_path)
    source_rows = len(raw.index)
    frame = _drop_empty_columns(raw)
    frame = frame.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all").fillna("")
    frame = normalize_dataframe_columns(frame)

    if len(set(frame.columns)) != len(frame.columns):
        duplicated = sorted({column for column in frame.columns if list(frame.columns).count(column) > 1})
        raise ImportValidationError(f"Nama kolom menjadi ganda setelah normalisasi: {', '.join(duplicated)}")

    read_columns = set(frame.columns)
    missing = REQUIRED_COLUMNS - read_columns
    if missing:
        raise ImportValidationError(
            "Format file tidak sesuai. Pastikan sheet SLS memiliki kolom kec_code, kec_name, desa_code, "
            "desa_name, subsls_code, subsls_name, PCL, PML, total, OPEN, dan DRAFT.",
            read_columns=read_columns,
            missing_columns=missing,
        )

    for column in IDENTITY_COLUMNS:
        if column not in frame:
            frame[column] = ""
        frame[column] = frame[column].map(clean_text)
    for column in DETAIL_STATUS_COLUMNS:
        if column not in frame:
            frame[column] = 0

    warnings: list[str] = []
    for column in NUMERIC_COLUMNS:
        frame[column] = _convert_numeric(frame[column], column, warnings)

    widths = {"prov": 2, "kab": 2, "kec_code": 3, "desa_code": 3, "subsls_code": 6}
    for column, width in widths.items():
        frame[column] = frame[column].map(lambda value: clean_code(value, width))

    validation_fields = {
        "kec_code": "Kode Kecamatan",
        "kec_name": "Nama Kecamatan",
        "desa_code": "Kode Desa",
        "desa_name": "Nama Desa",
        "subsls_code": "Kode Sub-SLS",
        "subsls_name": "Nama Sub-SLS",
        "nama_pcl": "PCL",
        "nama_pml": "PML",
    }
    row_errors = []
    for column, label in validation_fields.items():
        bad_rows = frame.index[frame[column].eq("")].tolist()
        if bad_rows:
            sample = ", ".join(str(item + 2) for item in bad_rows[:10])
            row_errors.append(f"{label} kosong pada baris {sample}")
    if row_errors:
        raise ImportValidationError("Data wajib tidak lengkap: " + "; ".join(row_errors))

    records = []
    for index, row in frame.iterrows():
        calculation = calculate_progress(row["total_target"], row["open_count"], row["draft_count"])
        if calculation.warning:
            warnings.append(f"Baris {index + 2}: {calculation.warning}")
        workflow_sum = sum(int(row[column]) for column in WORKFLOW_COLUMNS)
        if workflow_sum != int(row["total_target"]):
            warnings.append(f"Jumlah status workflow tidak sama dengan total pada baris {index + 2}.")
        sls_key = "-".join(
            [row["prov"], row["kab"], row["kec_code"], row["desa_code"], row["subsls_code"]]
        )
        record = {column: row[column] for column in IDENTITY_COLUMNS}
        record.update({column: int(row[column]) for column in NUMERIC_COLUMNS})
        record.update(
            {
                "sls_key": sls_key,
                "processed_count": calculation.processed,
                "remaining_count": calculation.remaining,
                "progress": calculation.progress,
                "progress_status": calculation.status,
            }
        )
        records.append(record)

    grouped_by_key: dict[str, list[dict]] = {}
    duplicate_rows = 0
    for record in records:
        group = grouped_by_key.setdefault(record["sls_key"], [])
        if any(previous == record for previous in group):
            duplicate_rows += 1
        else:
            group.append(record)

    unique_records: list[dict] = []
    conflicts = []
    assignment_columns = ("email_pcl", "username_pcl", "nama_pcl", "email_pml", "nama_pml")
    for base_key, group in grouped_by_key.items():
        if len(group) == 1:
            unique_records.append(group[0])
            continue

        identities = [
            tuple(clean_text(record[column]).lower() for column in assignment_columns)
            for record in group
        ]
        if len(set(identities)) != len(identities):
            conflicts.append(base_key)
            continue

        warnings.append(
            f"Kunci SLS {base_key} digunakan oleh {len(group)} penugasan PCL/PML berbeda; "
            "setiap penugasan disimpan sebagai baris terpisah."
        )
        for record, identity in zip(group, identities):
            suffix = hashlib.sha1("|".join(identity).encode("utf-8")).hexdigest()[:12]
            separated = record.copy()
            separated["sls_key"] = f"{base_key}-{suffix}"
            unique_records.append(separated)

    if conflicts:
        sample = ", ".join(sorted(set(conflicts))[:30])
        raise ImportValidationError(
            f"Ditemukan data SLS ganda dengan nilai yang berbeda. Periksa kembali file pada kode: {sample}"
        )

    return {
        "records": unique_records,
        "processed_sheet": processed_sheet,
        "source_rows": source_rows,
        "skipped_rows": source_rows - len(frame.index),
        "duplicate_rows": duplicate_rows,
        "warnings": warnings,
        "read_columns": sorted(read_columns),
    }


def _kecamatan_key(record):
    return record["prov"], record["kab"], record["kec_code"]


def _pml_key(record):
    return _kecamatan_key(record), record["email_pml"].lower(), record["nama_pml"].lower()


def _pcl_key(record):
    return (
        _pml_key(record),
        record["email_pcl"].lower(),
        record["username_pcl"].lower(),
        record["nama_pcl"].lower(),
    )


def import_prepared_data(prepared: dict) -> dict:
    records = prepared["records"]
    db.session.execute(delete(SLS))
    db.session.execute(delete(PCL))
    db.session.execute(delete(PML))
    db.session.execute(delete(Kecamatan))

    kec_objects = {}
    for record in records:
        key = _kecamatan_key(record)
        if key not in kec_objects:
            item = Kecamatan(
                prov_code=record["prov"],
                kab_code=record["kab"],
                kec_code=record["kec_code"],
                kec_name=record["kec_name"],
            )
            db.session.add(item)
            kec_objects[key] = item
    db.session.flush()

    pml_objects = {}
    for record in records:
        key = _pml_key(record)
        if key not in pml_objects:
            item = PML(
                kecamatan_id=kec_objects[_kecamatan_key(record)].id,
                email_pml=record["email_pml"].lower(),
                nama_pml=record["nama_pml"],
            )
            db.session.add(item)
            pml_objects[key] = item
    db.session.flush()

    pcl_objects = {}
    for record in records:
        key = _pcl_key(record)
        if key not in pcl_objects:
            item = PCL(
                kecamatan_id=kec_objects[_kecamatan_key(record)].id,
                pml_id=pml_objects[_pml_key(record)].id,
                email_pcl=record["email_pcl"].lower(),
                username_pcl=record["username_pcl"],
                nama_pcl=record["nama_pcl"],
            )
            db.session.add(item)
            pcl_objects[key] = item
    db.session.flush()

    sls_rows = []
    for record in records:
        sls_rows.append(
            {
                "kecamatan_id": kec_objects[_kecamatan_key(record)].id,
                "pml_id": pml_objects[_pml_key(record)].id,
                "pcl_id": pcl_objects[_pcl_key(record)].id,
                "prov_code": record["prov"],
                "kab_code": record["kab"],
                "desa_code": record["desa_code"],
                "desa_name": record["desa_name"],
                "subsls_code": record["subsls_code"],
                "subsls_name": record["subsls_name"],
                "sls_key": record["sls_key"],
                **{column: record[column] for column in NUMERIC_COLUMNS},
                "processed_count": record["processed_count"],
                "remaining_count": record["remaining_count"],
                "progress": record["progress"],
                "progress_status": record["progress_status"],
            }
        )
    for start in range(0, len(sls_rows), 750):
        db.session.execute(insert(SLS), sls_rows[start : start + 750])

    total_target = sum(row["total_target"] for row in records)
    total_processed = sum(row["processed_count"] for row in records)
    total_remaining = sum(row["remaining_count"] for row in records)
    return {
        "total_kecamatan": len(kec_objects),
        "total_pml": len(pml_objects),
        "total_pcl": len(pcl_objects),
        "total_sls": len(records),
        "total_target": total_target,
        "total_processed": total_processed,
        "total_remaining": total_remaining,
        "progress": aggregate_progress(total_target, total_processed),
    }
