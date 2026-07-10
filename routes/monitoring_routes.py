from flask import Blueprint, render_template, request

from services.monitoring_service import (
    filter_options,
    get_kecamatan_rows,
    get_pcl_rows,
    get_pml_rows,
    get_sls_rows,
)
from utils.decorators import login_required
from utils.helpers import filters_from_request


monitoring_bp = Blueprint("monitoring", __name__)


def _context(level, rows):
    filters = filters_from_request(request.args)
    return {
        "rows": rows(filters),
        "filters": filters,
        "filter_options": filter_options(filters.get("kec_code"), filters.get("pml_id")),
        "level": level,
    }


@monitoring_bp.route("/monitoring-sls")
@login_required
def monitoring_sls():
    return render_template("monitoring_sls.html", **_context("sls", get_sls_rows))


@monitoring_bp.route("/monitoring-pcl")
@login_required
def monitoring_pcl():
    return render_template("monitoring_pcl.html", **_context("pcl", get_pcl_rows))


@monitoring_bp.route("/monitoring-pml")
@login_required
def monitoring_pml():
    return render_template("monitoring_pml.html", **_context("pml", get_pml_rows))


@monitoring_bp.route("/monitoring-kecamatan")
@login_required
def monitoring_kecamatan():
    return render_template("monitoring_kecamatan.html", **_context("kecamatan", get_kecamatan_rows))

