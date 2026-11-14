from functools import wraps

from flask import Blueprint, abort, flash, jsonify, make_response, redirect, render_template, request, session, url_for

from extensions import db
from models.api_token import ApiToken
from services.monitoring_service import chart_data, dashboard_summary, filter_options, get_sls_datatable
from services.token_service import authenticate_bearer_token, create_api_token
from utils.decorators import admin_required, login_required
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


def bearer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        scheme, _, raw = request.headers.get("Authorization", "").partition(" ")
        token = authenticate_bearer_token(raw.strip()) if scheme.lower() == "bearer" else None
        if token is None:
            response = jsonify(error="Invalid or expired bearer token")
            response.status_code = 401
            response.headers["WWW-Authenticate"] = "Bearer"
            return response
        return view(*args, **kwargs)
    return wrapped


@api_bp.route("/api/v1/dashboard")
@bearer_required
def v1_dashboard():
    return jsonify(dashboard_summary())


@api_bp.route("/api/v1/monitoring/sls")
@bearer_required
def v1_sls():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(1000, max(1, request.args.get("per_page", 100, type=int)))
    result = get_sls_datatable(start=(page - 1) * per_page, length=per_page,
                               filters=filters_from_request(request.args))
    return jsonify(data=result["data"], total=result["recordsFiltered"], page=page, per_page=per_page)


@api_bp.route("/admin/api-tokens", methods=["GET", "POST"])
@admin_required
def tokens():
    raw = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        days = request.form.get("expires_days", type=int)
        if not name or len(name) > 100 or days is None or not 1 <= days <= 365:
            flash("Nama token wajib (maksimum 100 karakter), masa berlaku 1–365 hari.", "danger")
        else:
            _, raw = create_api_token(session["user_id"], name, days)
    rows = ApiToken.query.filter_by(user_id=session["user_id"]).order_by(ApiToken.id.desc()).all()
    response = make_response(render_template("api_tokens.html", tokens=rows, raw_token=raw))
    response.headers["Cache-Control"] = "no-store"
    return response


@api_bp.route("/admin/api-tokens/<int:token_id>/revoke", methods=["POST"])
@admin_required
def revoke_token(token_id):
    token = db.get_or_404(ApiToken, token_id)
    if token.user_id != session["user_id"]:
        abort(403)
    token.is_active = False
    db.session.commit()
    flash("Token dicabut.", "success")
    return redirect(url_for("api.tokens"))
