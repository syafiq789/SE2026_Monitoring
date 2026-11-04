from flask import Blueprint, jsonify, request

from services.monitoring_service import chart_data, dashboard_summary, filter_options
from utils.decorators import login_required


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


