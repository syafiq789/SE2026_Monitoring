from flask import Blueprint, jsonify, request

from services.monitoring_service import chart_data, dashboard_summary, filter_options, get_sls_rows
from utils.decorators import bearer_token_required, login_required
from utils.helpers import filters_from_request


api_bp = Blueprint("api", __name__)


@api_bp.route("/api/dashboard-data")
@login_required
def dashboard_data():
    return jsonify(dashboard_summary())


@api_bp.route("/api/chart-data")
@login_required
def charts():
    return jsonify(chart_data())


@api_bp.route("/api/filter-data")
@login_required
def filters():
    return jsonify(filter_options(request.args.get("kec_code", ""), request.args.get("pml_id", type=int)))


@api_bp.route("/api/v1/dashboard")
@bearer_token_required
def api_v1_dashboard():
    return jsonify({"data": dashboard_summary()})


@api_bp.route("/api/v1/monitoring/sls")
@bearer_token_required
def api_v1_sls():
    rows = get_sls_rows(filters_from_request(request.args))
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 100, type=int), 1), 1000)
    start = (page - 1) * per_page
    return jsonify(
        {"data": rows[start : start + per_page], "meta": {"page": page, "per_page": per_page, "total": len(rows)}}
    )

