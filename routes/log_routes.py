from flask import Blueprint, render_template, request
from services.activity_service import get_activity_logs
from utils.decorators import admin_required, login_required

log_bp = Blueprint("logs", __name__)


@log_bp.route("/admin/logs")
@login_required
@admin_required
def activity_logs():
    """
    Halaman Audit Trail & Log Aktivitas Sistem (Khusus Role Admin).
    """
    action_filter = request.args.get("action", "").strip() or None
    search_query = request.args.get("q", "").strip() or None

    logs = get_activity_logs(limit=250, action_filter=action_filter, search=search_query)

    return render_template(
        "activity_logs.html",
        logs=logs,
        current_action=action_filter or "",
        search_query=search_query or "",
    )
