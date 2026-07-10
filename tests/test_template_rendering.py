from types import SimpleNamespace

from flask import render_template

from app import create_app


def test_key_templates_render_and_endpoints_resolve():
    app = create_app()
    user = SimpleNamespace(nama_lengkap="Administrator", role="admin")
    filters = {
        "kec_code": "010", "desa_code": "", "pml_id": None, "pcl_id": None,
        "status": "", "progress_min": None, "progress_max": None,
    }
    options = {"kecamatan": [], "desa": [], "pml": [], "pcl": []}
    with app.test_request_context("/monitoring-sls?kec_code=010"):
        html = render_template(
            "monitoring_sls.html", current_user=user, rows=[], filters=filters,
            filter_options=options, level="sls",
        )
        assert "/export/sls/excel?kec_code=010" in html
    with app.test_request_context("/download"):
        html = render_template("download.html", current_user=user)
        assert "/export/kecamatan/excel" in html
        assert "/export/pml/csv" in html

