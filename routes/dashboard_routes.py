from flask import Blueprint, render_template

from services.monitoring_service import dashboard_summary
from utils.decorators import login_required


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", summary=dashboard_summary())

