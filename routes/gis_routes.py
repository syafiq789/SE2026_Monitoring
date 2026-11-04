from flask import Blueprint, jsonify, render_template
from services.gis_service import get_gis_monitoring_data
from utils.decorators import login_required

gis_bp = Blueprint("gis", __name__)


@gis_bp.route("/peta-spasial")
@login_required
def peta_spasial():
    """
    Halaman Visualisasi Peta Spasial (WebGIS) Banyuwangi untuk monitoring sebaran progres.
    """
    gis_data = get_gis_monitoring_data()
    return render_template(
        "peta_spasial.html",
        features=gis_data["features"],
        summary=gis_data["summary"],
        leaderboard_top=gis_data["leaderboard_top"],
        leaderboard_bottom=gis_data["leaderboard_bottom"],
    )


@gis_bp.route("/api/gis/kecamatan")
@login_required
def api_gis_kecamatan():
    """
    API endpoint data spasial kecamatan untuk rendering layer peta Leaflet.js secara realtime.
    """
    return jsonify(get_gis_monitoring_data())
