from pathlib import Path

from app import create_app


def test_required_routes_are_registered():
    app = create_app()
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required = {
        "/", "/login", "/register", "/logout", "/dashboard",
        "/monitoring-sls", "/monitoring-pcl", "/monitoring-pml", "/monitoring-kecamatan",
        "/upload", "/upload-data", "/download", "/riwayat-upload",
        "/admin/users", "/admin/register", "/api/dashboard-data", "/api/chart-data", "/api/filter-data",
        "/export/sls/csv", "/export/sls/excel", "/export/pcl/csv", "/export/pcl/excel",
        "/export/pml/csv", "/export/pml/excel", "/export/kecamatan/csv", "/export/kecamatan/excel",
    }
    assert required.issubset(routes)


def test_database_schema_contains_all_tables_and_views():
    sql = (Path(__file__).parents[1] / "database.sql").read_text(encoding="utf-8").lower()
    for table in ("users", "kecamatan", "pml", "pcl", "sls", "upload_history", "api_tokens"):
        assert f"create table if not exists {table}" in sql
    for view in (
        "view_dashboard_summary", "view_monitoring_sls", "view_monitoring_pcl",
        "view_monitoring_pml", "view_monitoring_kecamatan",
    ):
        assert f"create or replace view {view}" in sql

