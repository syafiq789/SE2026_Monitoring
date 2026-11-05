from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)

from services.monitoring_service import (
    chart_data,
    filter_options,
    get_kecamatan_rows,
    get_pcl_rows,
    get_pml_rows,
    get_sls_count,
    get_sls_datatable,
    get_sls_rows,
)
from utils.decorators import login_required
from utils.helpers import filters_from_request


monitoring_bp = Blueprint(
    "monitoring",
    __name__,
)


def _context(level, rows_function):
    filters = filters_from_request(
        request.args
    )

    rows = rows_function(filters)

    return {
        "rows": rows,
        "filters": filters,
        "filter_options": filter_options(
            filters.get("kec_code"),
            filters.get("pml_id"),
        ),
        "level": level,
    }


@monitoring_bp.route(
    "/monitoring-sls"
)
@login_required
def monitoring_sls():
    filters = filters_from_request(request.args)
    count = get_sls_count(filters)
    return render_template(
        "monitoring_sls.html",
        rows=[],
        rows_count=count,
        filters=filters,
        filter_options=filter_options(
            filters.get("kec_code"),
            filters.get("pml_id"),
        ),
        level="sls",
    )


@monitoring_bp.route(
    "/api/monitoring/sls-dt"
)
@login_required
def sls_datatable():
    draw = request.args.get("draw", 1, type=int)
    start = request.args.get("start", 0, type=int)
    length = request.args.get("length", 25, type=int)
    search_value = request.args.get("search[value]", "", type=str)
    order_col = request.args.get("order[0][column]", 1, type=int)
    order_dir = request.args.get("order[0][dir]", "asc", type=str)
    filters = filters_from_request(request.args)

    result = get_sls_datatable(
        draw=draw,
        start=start,
        length=length,
        search_value=search_value,
        order_col=order_col,
        order_dir=order_dir,
        filters=filters,
    )
    return jsonify(result)


@monitoring_bp.route(
    "/monitoring-pcl"
)
@login_required
def monitoring_pcl():
    return render_template(
        "monitoring_pcl.html",
        **_context(
            "pcl",
            get_pcl_rows,
        ),
    )


@monitoring_bp.route(
    "/monitoring-pml"
)
@login_required
def monitoring_pml():
    return render_template(
        "monitoring_pml.html",
        **_context(
            "pml",
            get_pml_rows,
        ),
    )


@monitoring_bp.route(
    "/monitoring-kecamatan"
)
@login_required
def monitoring_kecamatan():
    return render_template(
        "monitoring_kecamatan.html",
        **_context(
            "kecamatan",
            get_kecamatan_rows,
        ),
    )


@monitoring_bp.route(
    "/api/chart-data"
)
@login_required
def api_chart_data():
    return jsonify(
        chart_data()
    )