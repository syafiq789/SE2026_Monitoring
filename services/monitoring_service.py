from sqlalchemy import distinct, func

from extensions import db
from models.monitoring import Kecamatan, PCL, PML, SLS
from utils.calculations import aggregate_progress


def _apply_filters(query, filters: dict, grouped=False):
    """
    Menerapkan filter yang berasal dari halaman monitoring.
    """

    if filters.get("kec_code"):
        query = query.filter(
            Kecamatan.kec_code == filters["kec_code"]
        )

    if filters.get("desa_code"):
        query = query.filter(
            SLS.desa_code == filters["desa_code"]
        )

    if filters.get("pml_id"):
        query = query.filter(
            SLS.pml_id == filters["pml_id"]
        )

    if filters.get("pcl_id"):
        query = query.filter(
            SLS.pcl_id == filters["pcl_id"]
        )

    if filters.get("status"):
        query = query.filter(
            SLS.progress_status == filters["status"]
        )

    if not grouped:
        if filters.get("progress_min") is not None:
            query = query.filter(
                SLS.progress >= filters["progress_min"]
            )

        if filters.get("progress_max") is not None:
            query = query.filter(
                SLS.progress <= filters["progress_max"]
            )

    return query


def get_sls_rows(filters=None):
    """
    Mengambil seluruh data SLS beserta Kecamatan, PML, dan PCL.
    """

    filters = filters or {}

    query = (
        db.session.query(
            SLS,
            Kecamatan,
            PML,
            PCL,
        )
        .join(
            Kecamatan,
            SLS.kecamatan_id == Kecamatan.id,
        )
        .join(
            PML,
            SLS.pml_id == PML.id,
        )
        .join(
            PCL,
            SLS.pcl_id == PCL.id,
        )
    )

    query = _apply_filters(query, filters)

    rows = []

    query_result = query.order_by(
        Kecamatan.kec_code,
        SLS.desa_code,
        SLS.subsls_code,
    ).all()

    for sls, kecamatan, pml, pcl in query_result:
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
                "approved_by_pengawas": (
                    sls.approved_by_pengawas
                ),
                "progress": float(
                    sls.progress or 0
                ),
                "progress_status": (
                    sls.progress_status
                ),
                "completed_by_admin_kabupaten": (
                    sls.completed_by_admin_kabupaten
                ),
                "edited_by_admin_kabupaten": (
                    sls.edited_by_admin_kabupaten
                ),
                "edited_by_pengawas": (
                    sls.edited_by_pengawas
                ),
                "rejected_by_admin_kabupaten": (
                    sls.rejected_by_admin_kabupaten
                ),
                "rejected_by_pengawas": (
                    sls.rejected_by_pengawas
                ),
                "revoked_by_admin_kabupaten": (
                    sls.revoked_by_admin_kabupaten
                ),
                "revoked_by_pengawas": (
                    sls.revoked_by_pengawas
                ),
                "submitted_by_pencacah": (
                    sls.submitted_by_pencacah
                ),
                "submitted_respondent": (
                    sls.submitted_respondent
                ),
            }
        )

    return rows


def _aggregate_base(
    group_columns,
    extra_columns=None,
    filters=None,
):
    """
    Query dasar untuk rekap Kecamatan, PML, dan PCL.
    """

    filters = filters or {}

    columns = (
        list(group_columns)
        + list(extra_columns or [])
    )

    query = (
        db.session.query(
            *columns,
            func.count(
                distinct(SLS.id)
            ).label("jumlah_sls"),
            func.sum(
                SLS.total_target
            ).label("total_target"),
            func.sum(
                SLS.open_count
            ).label("open_count"),
            func.sum(
                SLS.draft_count
            ).label("draft_count"),
            func.sum(
                SLS.processed_count
            ).label("processed_count"),
            func.sum(
                SLS.remaining_count
            ).label("remaining_count"),
            func.sum(
                SLS.approved_by_pengawas
            ).label("approved_count"),
        )
        .select_from(SLS)
        .join(
            Kecamatan,
            SLS.kecamatan_id == Kecamatan.id,
        )
        .join(
            PML,
            SLS.pml_id == PML.id,
        )
        .join(
            PCL,
            SLS.pcl_id == PCL.id,
        )
    )

    query = _apply_filters(
        query,
        filters,
        grouped=True,
    ).group_by(*group_columns)

    progress_expression = (
        func.sum(SLS.processed_count)
        / func.nullif(
            func.sum(SLS.total_target),
            0,
        )
        * 100
    )

    if filters.get("progress_min") is not None:
        query = query.having(
            progress_expression
            >= filters["progress_min"]
        )

    if filters.get("progress_max") is not None:
        query = query.having(
            progress_expression
            <= filters["progress_max"]
        )

    return query


def _row_metrics(row):
    """
    Mengubah hasil SQLAlchemy menjadi dictionary
    dan menghitung progress agregat.
    """

    data = dict(row._mapping)

    data["total_target"] = int(
        data.get("total_target") or 0
    )

    data["processed_count"] = int(
        data.get("processed_count") or 0
    )

    integer_fields = (
        "jumlah_sls",
        "jumlah_pml",
        "jumlah_pcl",
        "open_count",
        "draft_count",
        "remaining_count",
        "approved_count",
    )

    for key in integer_fields:
        if key in data:
            data[key] = int(
                data.get(key) or 0
            )

    data["progress"] = aggregate_progress(
        data["total_target"],
        data["processed_count"],
    )

    return data


def get_pcl_rows(filters=None):
    """
    Rekap progress per PCL.
    """

    query = _aggregate_base(
        [
            PCL.id,
            PCL.pml_id.label("pml_id"),
            Kecamatan.kec_code,
            Kecamatan.kec_name,
            PML.nama_pml,
            PCL.nama_pcl,
        ],
        filters=filters,
    )

    rows = query.order_by(
        Kecamatan.kec_code,
        PCL.nama_pcl,
    ).all()

    return [
        _row_metrics(row)
        for row in rows
    ]


def get_pml_rows(filters=None):
    """
    Rekap progress per PML.
    """

    query = _aggregate_base(
        [
            PML.id,
            Kecamatan.kec_code,
            Kecamatan.kec_name,
            PML.nama_pml,
        ],
        extra_columns=[
            func.count(
                distinct(PCL.id)
            ).label("jumlah_pcl"),
        ],
        filters=filters,
    )

    rows = query.order_by(
        Kecamatan.kec_code,
        PML.nama_pml,
    ).all()

    return [
        _row_metrics(row)
        for row in rows
    ]


def get_kecamatan_rows(filters=None):
    """
    Rekap progress per Kecamatan.
    """

    query = _aggregate_base(
        [
            Kecamatan.id,
            Kecamatan.kec_code,
            Kecamatan.kec_name,
        ],
        extra_columns=[
            func.count(
                distinct(PML.id)
            ).label("jumlah_pml"),
            func.count(
                distinct(PCL.id)
            ).label("jumlah_pcl"),
        ],
        filters=filters,
    )

    rows = query.order_by(
        Kecamatan.kec_code
    ).all()

    return [
        _row_metrics(row)
        for row in rows
    ]


def dashboard_summary():
    """
    Mengambil ringkasan utama dashboard.
    """

    metrics = (
        db.session.query(
            func.count(
                distinct(Kecamatan.id)
            ).label("total_kecamatan"),
            func.count(
                distinct(PML.id)
            ).label("total_pml"),
            func.count(
                distinct(PCL.id)
            ).label("total_pcl"),
            func.count(
                distinct(SLS.id)
            ).label("total_sls"),
            func.coalesce(
                func.sum(SLS.total_target),
                0,
            ).label("total_target"),
            func.coalesce(
                func.sum(SLS.processed_count),
                0,
            ).label("total_processed"),
            func.coalesce(
                func.sum(SLS.remaining_count),
                0,
            ).label("total_remaining"),
        )
        .select_from(SLS)
        .outerjoin(
            Kecamatan,
            SLS.kecamatan_id == Kecamatan.id,
        )
        .outerjoin(
            PML,
            SLS.pml_id == PML.id,
        )
        .outerjoin(
            PCL,
            SLS.pcl_id == PCL.id,
        )
        .one()
    )

    result = {
        key: int(value or 0)
        for key, value
        in metrics._mapping.items()
    }

    result["progress"] = aggregate_progress(
        result["total_target"],
        result["total_processed"],
    )

    statuses = dict(
        db.session.query(
            SLS.progress_status,
            func.count(SLS.id),
        )
        .group_by(SLS.progress_status)
        .all()
    )

    result.update(
        {
            "sls_data_kosong": int(
                statuses.get(
                    "Data Kosong",
                    0,
                )
            ),
            "sls_belum_mulai": int(
                statuses.get(
                    "Belum Mulai",
                    0,
                )
            ),
            "sls_sedang_proses": int(
                statuses.get(
                    "Sedang Proses",
                    0,
                )
            ),
            "sls_selesai": int(
                statuses.get(
                    "Selesai",
                    0,
                )
            ),
        }
    )

    return result


def chart_data(kec_code=None, sort_order="asc"):
    """
    Menyediakan data seluruh grafik dashboard.

    Parameter:
    - kec_code: kode kecamatan opsional.
    - sort_order: "asc" untuk progres terendah ke tertinggi,
      atau "desc" untuk progres tertinggi ke terendah.

    Data Kecamatan, PML, dan PCL membawa ID/kode agar setiap
    batang grafik dapat diklik dan dapat difilter di dashboard.
    """

    selected_kec_code = str(kec_code or "").strip()
    normalized_sort = str(sort_order or "asc").strip().lower()

    if normalized_sort not in {"asc", "desc"}:
        normalized_sort = "asc"

    chart_filters = {}

    if selected_kec_code:
        chart_filters["kec_code"] = selected_kec_code

    kecamatan_rows = get_kecamatan_rows(chart_filters)
    pml_rows = get_pml_rows(chart_filters)
    pcl_rows = get_pcl_rows(chart_filters)

    workflow_query = db.session.query(
        func.coalesce(
            func.sum(SLS.approved_by_pengawas),
            0,
        ).label("APPROVED"),

        func.coalesce(
            func.sum(
                SLS.completed_by_admin_kabupaten
            ),
            0,
        ).label("COMPLETED"),

        func.coalesce(
            func.sum(SLS.draft_count),
            0,
        ).label("DRAFT"),

        func.coalesce(
            func.sum(
                func.coalesce(
                    SLS.edited_by_admin_kabupaten,
                    0,
                )
                + func.coalesce(
                    SLS.edited_by_pengawas,
                    0,
                )
            ),
            0,
        ).label("EDITED"),

        func.coalesce(
            func.sum(SLS.open_count),
            0,
        ).label("OPEN"),

        func.coalesce(
            func.sum(
                func.coalesce(
                    SLS.rejected_by_admin_kabupaten,
                    0,
                )
                + func.coalesce(
                    SLS.rejected_by_pengawas,
                    0,
                )
            ),
            0,
        ).label("REJECTED"),

        func.coalesce(
            func.sum(
                func.coalesce(
                    SLS.revoked_by_admin_kabupaten,
                    0,
                )
                + func.coalesce(
                    SLS.revoked_by_pengawas,
                    0,
                )
            ),
            0,
        ).label("REVOKED"),

        func.coalesce(
            func.sum(
                func.coalesce(
                    SLS.submitted_by_pencacah,
                    0,
                )
                + func.coalesce(
                    SLS.submitted_respondent,
                    0,
                )
            ),
            0,
        ).label("SUBMITTED"),
    )

    if selected_kec_code:
        workflow_query = (
            workflow_query
            .select_from(SLS)
            .join(
                Kecamatan,
                SLS.kecamatan_id == Kecamatan.id,
            )
            .filter(
                Kecamatan.kec_code == selected_kec_code
            )
        )

    workflow_result = workflow_query.one()

    data_kecamatan = [
        {
            "id": row["id"],
            "kec_code": row["kec_code"],
            "kec_name": row["kec_name"],
            "label": row["kec_name"],
            "progress": float(
                row["progress"] or 0
            ),
        }
        for row in kecamatan_rows
    ]

    data_pml = [
        {
            "pml_id": row["id"],
            "kec_code": row["kec_code"],
            "kec_name": row["kec_name"],
            "label": row["nama_pml"],
            "progress": float(
                row["progress"] or 0
            ),
        }
        for row in pml_rows
    ]

    data_pcl = [
        {
            "pcl_id": row["id"],
            "pml_id": row["pml_id"],
            "kec_code": row["kec_code"],
            "kec_name": row["kec_name"],
            "nama_pml": row["nama_pml"],
            "label": row["nama_pcl"],
            "progress": float(
                row["progress"] or 0
            ),
        }
        for row in pcl_rows
    ]

    reverse_sort = normalized_sort == "desc"

    data_kecamatan.sort(
        key=lambda item: item["progress"],
        reverse=reverse_sort,
    )

    data_pml.sort(
        key=lambda item: item["progress"],
        reverse=reverse_sort,
    )

    data_pcl.sort(
        key=lambda item: item["progress"],
        reverse=reverse_sort,
    )

    workflow_mapping = dict(
        workflow_result._mapping
    )

    workflow_order = [
        "APPROVED",
        "COMPLETED",
        "DRAFT",
        "EDITED",
        "OPEN",
        "REJECTED",
        "REVOKED",
        "SUBMITTED",
    ]

    data_workflow = [
        {
            "key": key,
            "label": key,
            "value": int(
                workflow_mapping.get(key) or 0
            ),
        }
        for key in workflow_order
    ]

    # Daftar kecamatan selalu dikirim lengkap untuk isi dropdown dashboard.
    kecamatan_options = [
        {
            "code": item.kec_code,
            "name": item.kec_name,
        }
        for item in Kecamatan.query.order_by(
            Kecamatan.kec_name
        ).all()
    ]

    return {
        "selected_kec_code": selected_kec_code,
        "sort_order": normalized_sort,
        "kecamatan_options": kecamatan_options,
        "kecamatan": data_kecamatan,
        "pml": data_pml,
        "pcl": data_pcl,
        "workflow": data_workflow,

        # Mengikuti pilihan ascending/descending dari dashboard.
        "kecamatan_terendah": list(data_kecamatan),

        # Tetap menampilkan 10 PML paling rendah.
        "pml_terendah": sorted(
            data_pml,
            key=lambda item: item["progress"],
        )[:10],
    }



def filter_options(
    kec_code="",
    pml_id=None,
):
    """
    Menyediakan pilihan filter untuk halaman monitoring.
    """

    kecamatan = Kecamatan.query.order_by(
        Kecamatan.kec_code
    ).all()

    desa_query = db.session.query(
        SLS.desa_code,
        SLS.desa_name,
    ).distinct()

    pml_query = PML.query.join(
        Kecamatan
    )

    pcl_query = PCL.query.join(
        Kecamatan
    )

    if kec_code:
        desa_query = (
            desa_query
            .join(
                Kecamatan,
                SLS.kecamatan_id
                == Kecamatan.id,
            )
            .filter(
                Kecamatan.kec_code
                == kec_code
            )
        )

        pml_query = pml_query.filter(
            Kecamatan.kec_code
            == kec_code
        )

        pcl_query = pcl_query.filter(
            Kecamatan.kec_code
            == kec_code
        )

    if pml_id:
        pcl_query = pcl_query.filter(
            PCL.pml_id == pml_id
        )

    return {
        "kecamatan": [
            {
                "code": item.kec_code,
                "name": item.kec_name,
            }
            for item in kecamatan
        ],

        "desa": [
            {
                "code": code,
                "name": name,
            }
            for code, name
            in desa_query.order_by(
                SLS.desa_code
            ).all()
        ],

        "pml": [
            {
                "id": item.id,
                "name": item.nama_pml,
            }
            for item
            in pml_query.order_by(
                PML.nama_pml
            ).all()
        ],

        "pcl": [
            {
                "id": item.id,
                "name": item.nama_pcl,
            }
            for item
            in pcl_query.order_by(
                PCL.nama_pcl
            ).all()
        ],
    }