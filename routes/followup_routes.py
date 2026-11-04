from flask import Blueprint, jsonify, render_template, request, session

from services.activity_service import log_activity
from services.followup_service import get_followup_data
from utils.decorators import login_required

followup_bp = Blueprint("followup", __name__)


@followup_bp.route("/tindak-lanjut")
@login_required
def tindak_lanjut():
    pml_id_raw = request.args.get("pml_id", "").strip()
    pml_id = int(pml_id_raw) if pml_id_raw.isdigit() else None

    filters = {
        "kec_code": request.args.get("kec_code", "").strip(),
        "pml_id": pml_id,
        "role_type": request.args.get("role_type", "pcl").strip().lower(),
        "priority": request.args.get("priority", "").strip().lower(),
        "q": request.args.get("q", "").strip(),
    }

    context = get_followup_data(filters)
    return render_template("tindak_lanjut.html", **context)


@followup_bp.route("/api/followup/log", methods=["POST"])
@login_required
def api_log_followup():
    payload = request.get_json(silent=True) or {}
    channel = str(payload.get("channel") or "WHATSAPP").strip().upper()
    target_name = str(payload.get("target_name") or "Petugas").strip()
    kec_name = str(payload.get("kec_name") or "-").strip()
    progress = payload.get("progress")

    details = f"Kirim pengingat ({channel}) ke {target_name} - Kec. {kec_name}"
    if progress is not None:
        details += f" (Progres: {progress}%)"

    log_activity(
        user_id=session.get("user_id"),
        action=f"FOLLOWUP_{channel}",
        target=target_name[:100],
        details=details,
        ip_address=request.remote_addr,
    )
    return jsonify({"status": "ok", "message": "Riwayat tindak lanjut tercatat di Audit Log."})

