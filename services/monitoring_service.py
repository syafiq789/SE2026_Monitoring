from sqlalchemy import distinct, func

from extensions import db
from models.monitoring import Kecamatan, PCL, PML, SLS
from utils.calculations import aggregate_progress


def _apply_filters(query, filters: dict, grouped=False):
    if filters.get("kec_code"):
        query = query.filter(Kecamatan.kec_code == filters["kec_code"])
    if filters.get("desa_code"):
        query = query.filter(SLS.desa_code == filters["desa_code"])
    if filters.get("pml_id"):
        query = query.filter(SLS.pml_id == filters["pml_id"])
    if filters.get("pcl_id"):
        query = query.filter(SLS.pcl_id == filters["pcl_id"])
    if filters.get("status"):
        query = query.filter(SLS.progress_status == filters["status"])
    if not grouped:
        if filters.get("progress_min") is not None:
            query = query.filter(SLS.progress >= filters["progress_min"])
        if filters.get("progress_max") is not None:
            query = query.filter(SLS.progress <= filters["progress_max"])
    return query


def get_sls_rows(filters=None):
    filters = filters or {}
    query = (
        db.session.query(SLS, Kecamatan, PML, PCL)
        .join(Kecamatan, SLS.kecamatan_id == Kecamatan.id)
        .join(PML, SLS.pml_id == PML.id)
        .join(PCL, SLS.pcl_id == PCL.id)
    )
    query = _apply_filters(query, filters)
    rows = []
    for sls, kecamatan, pml, pcl in query.order_by(
        Kecamatan.kec_code, SLS.desa_code, SLS.subsls_code
    ).all():
        rows.append(
            {
                "id": sls.id,
                "prov_code": sls.prov_code,
                "kab_code": sls.kab_code,
                "kec_code": kecamatan.kec_code,
                "kec_name": kecamatan.kec_name,
                "desa_code": sls.desa_code,
                "desa_name": sls.desa_name,
                "subsls_code": sls.subsls_code,
                "subsls_name": sls.subsls_name,
                "pml_id": pml.id,
                "nama_pml": pml.nama_pml,
                "pcl_id": pcl.id,
                "nama_pcl": pcl.nama_pcl,
                "email_pml": pml.email_pml,
                "email_pcl": pcl.email_pcl,
                "username_pcl": pcl.username_pcl,
                "total_target": sls.total_target,
                "open_count": sls.open_count,
                "draft_count": sls.draft_count,
                "processed_count": sls.processed_count,
                "remaining_count": sls.remaining_count,
                "approved_by_pengawas": sls.approved_by_pengawas,
                "progress": float(sls.progress),
                "progress_status": sls.progress_status,
                "completed_by_admin_kabupaten": sls.completed_by_admin_kabupaten,
                "edited_by_admin_kabupaten": sls.edited_by_admin_kabupaten,
                "edited_by_pengawas": sls.edited_by_pengawas,
                "rejected_by_admin_kabupaten": sls.rejected_by_admin_kabupaten,
                "rejected_by_pengawas": sls.rejected_by_pengawas,
                "revoked_by_admin_kabupaten": sls.revoked_by_admin_kabupaten,
                "revoked_by_pengawas": sls.revoked_by_pengawas,
                "submitted_by_pencacah": sls.submitted_by_pencacah,
                "submitted_respondent": sls.submitted_respondent,
            }
        )
    return rows


def _aggregate_base(group_columns, extra_columns=None, filters=None):
    filters = filters or {}
    columns = list(group_columns) + list(extra_columns or [])
    query = (
        db.session.query(
            *columns,
            func.count(distinct(SLS.id)).label("jumlah_sls"),
            func.sum(SLS.total_target).label("total_target"),
            func.sum(SLS.open_count).label("open_count"),
            func.sum(SLS.draft_count).label("draft_count"),
            func.sum(SLS.processed_count).label("processed_count"),
            func.sum(SLS.remaining_count).label("remaining_count"),
            func.sum(SLS.approved_by_pengawas).label("approved_count"),
        )
        .select_from(SLS)
        .join(Kecamatan, SLS.kecamatan_id == Kecamatan.id)
        .join(PML, SLS.pml_id == PML.id)
        .join(PCL, SLS.pcl_id == PCL.id)
    )
    query = _apply_filters(query, filters, grouped=True).group_by(*group_columns)
    progress_expression = func.sum(SLS.processed_count) / func.nullif(func.sum(SLS.total_target), 0) * 100
    if filters.get("progress_min") is not None:
        query = query.having(progress_expression >= filters["progress_min"])
    if filters.get("progress_max") is not None:
        query = query.having(progress_expression <= filters["progress_max"])
    return query


def _row_metrics(row):
    data = dict(row._mapping)
    data["total_target"] = int(data.get("total_target") or 0)
    data["processed_count"] = int(data.get("processed_count") or 0)
    for key in ("jumlah_sls", "open_count", "draft_count", "remaining_count", "approved_count"):
        if key in data:
            data[key] = int(data[key] or 0)
    data["progress"] = aggregate_progress(data["total_target"], data["processed_count"])
    return data


def get_pcl_rows(filters=None):
    query = _aggregate_base(
        [PCL.id, Kecamatan.kec_code, Kecamatan.kec_name, PML.nama_pml, PCL.nama_pcl],
        filters=filters,
    )
    return [_row_metrics(row) for row in query.order_by(Kecamatan.kec_code, PCL.nama_pcl).all()]


def get_pml_rows(filters=None):
    query = _aggregate_base(
        [PML.id, Kecamatan.kec_code, Kecamatan.kec_name, PML.nama_pml],
        extra_columns=[func.count(distinct(PCL.id)).label("jumlah_pcl")],
        filters=filters,
    )
    return [_row_metrics(row) for row in query.order_by(Kecamatan.kec_code, PML.nama_pml).all()]


def get_kecamatan_rows(filters=None):
    query = _aggregate_base(
        [Kecamatan.id, Kecamatan.kec_code, Kecamatan.kec_name],
        extra_columns=[
            func.count(distinct(PML.id)).label("jumlah_pml"),
            func.count(distinct(PCL.id)).label("jumlah_pcl"),
        ],
        filters=filters,
    )
    return [_row_metrics(row) for row in query.order_by(Kecamatan.kec_code).all()]


def dashboard_summary():
    metrics = db.session.query(
        func.count(distinct(Kecamatan.id)).label("total_kecamatan"),
        func.count(distinct(PML.id)).label("total_pml"),
        func.count(distinct(PCL.id)).label("total_pcl"),
        func.count(distinct(SLS.id)).label("total_sls"),
        func.coalesce(func.sum(SLS.total_target), 0).label("total_target"),
        func.coalesce(func.sum(SLS.processed_count), 0).label("total_processed"),
        func.coalesce(func.sum(SLS.remaining_count), 0).label("total_remaining"),
    ).select_from(SLS).outerjoin(Kecamatan, SLS.kecamatan_id == Kecamatan.id).outerjoin(
        PML, SLS.pml_id == PML.id
    ).outerjoin(PCL, SLS.pcl_id == PCL.id).one()
    result = {key: int(value or 0) for key, value in metrics._mapping.items()}
    result["progress"] = aggregate_progress(result["total_target"], result["total_processed"])
    statuses = dict(
        db.session.query(SLS.progress_status, func.count(SLS.id)).group_by(SLS.progress_status).all()
    )
    result.update(
        {
            "sls_data_kosong": statuses.get("Data Kosong", 0),
            "sls_belum_mulai": statuses.get("Belum Mulai", 0),
            "sls_sedang_proses": statuses.get("Sedang Proses", 0),
            "sls_selesai": statuses.get("Selesai", 0),
        }
    )
    return result


def chart_data():
    kecamatan = get_kecamatan_rows()
    pml = get_pml_rows()
    pcl = get_pcl_rows()
    workflow = db.session.query(
        func.coalesce(func.sum(SLS.open_count), 0).label("OPEN"),
        func.coalesce(func.sum(SLS.draft_count), 0).label("DRAFT"),
        func.coalesce(func.sum(SLS.approved_by_pengawas), 0).label("APPROVED"),
        func.coalesce(func.sum(SLS.completed_by_admin_kabupaten), 0).label("COMPLETED"),
        func.coalesce(func.sum(SLS.edited_by_admin_kabupaten + SLS.edited_by_pengawas), 0).label("EDITED"),
        func.coalesce(func.sum(SLS.rejected_by_admin_kabupaten + SLS.rejected_by_pengawas), 0).label("REJECTED"),
        func.coalesce(func.sum(SLS.revoked_by_admin_kabupaten + SLS.revoked_by_pengawas), 0).label("REVOKED"),
        func.coalesce(func.sum(SLS.submitted_by_pencacah + SLS.submitted_respondent), 0).label("SUBMITTED"),
    ).one()
    return {
        "kecamatan": [{"label": row["kec_name"], "progress": row["progress"]} for row in kecamatan],
        "pml": [{"label": row["nama_pml"], "progress": row["progress"]} for row in pml],
        "pcl": [{"label": row["nama_pcl"], "progress": row["progress"]} for row in pcl],
        "workflow": {key: int(value or 0) for key, value in workflow._mapping.items()},
        "kecamatan_terendah": sorted(
            [{"label": row["kec_name"], "progress": row["progress"]} for row in kecamatan],
            key=lambda item: item["progress"],
        )[:10],
        "pml_terendah": sorted(
            [{"label": row["nama_pml"], "progress": row["progress"]} for row in pml],
            key=lambda item: item["progress"],
        )[:10],
    }


def filter_options(kec_code="", pml_id=None):
    kecamatan = Kecamatan.query.order_by(Kecamatan.kec_code).all()
    desa_query = db.session.query(SLS.desa_code, SLS.desa_name).distinct()
    pml_query = PML.query.join(Kecamatan)
    pcl_query = PCL.query.join(Kecamatan)
    if kec_code:
        desa_query = desa_query.join(Kecamatan, SLS.kecamatan_id == Kecamatan.id).filter(Kecamatan.kec_code == kec_code)
        pml_query = pml_query.filter(Kecamatan.kec_code == kec_code)
        pcl_query = pcl_query.filter(Kecamatan.kec_code == kec_code)
    if pml_id:
        pcl_query = pcl_query.filter(PCL.pml_id == pml_id)
    return {
        "kecamatan": [{"code": item.kec_code, "name": item.kec_name} for item in kecamatan],
        "desa": [{"code": code, "name": name} for code, name in desa_query.order_by(SLS.desa_code).all()],
        "pml": [{"id": item.id, "name": item.nama_pml} for item in pml_query.order_by(PML.nama_pml).all()],
        "pcl": [{"id": item.id, "name": item.nama_pcl} for item in pcl_query.order_by(PCL.nama_pcl).all()],
    }
