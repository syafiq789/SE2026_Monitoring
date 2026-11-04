from services.followup_service import (
    build_kecamatan_broadcast_message,
    build_pcl_reminder_message,
    build_pml_reminder_message,
    classify_priority,
)
from services.gis_service import BANYUWANGI_KECAMATAN_COORDINATES, _get_status_color


def test_gis_coordinates_coverage():
    assert len(BANYUWANGI_KECAMATAN_COORDINATES) == 25
    assert "160" in BANYUWANGI_KECAMATAN_COORDINATES  # Banyuwangi Kota
    assert "090" in BANYUWANGI_KECAMATAN_COORDINATES  # Genteng
    assert "050" in BANYUWANGI_KECAMATAN_COORDINATES  # Muncar

    # Uji pewarnaan status
    assert _get_status_color(85.0) == "#25835b"
    assert _get_status_color(65.0) == "#dba63a"
    assert _get_status_color(30.0) == "#bf3f32"


def test_followup_priority_and_messages():
    p0 = classify_priority(0.0)
    assert p0["key"] == "belum_mulai"

    p_kritis = classify_priority(35.0)
    assert p_kritis["key"] == "kritis"

    pcl_msg = build_pcl_reminder_message(
        {
            "nama_pcl": "Budi Santoso",
            "kec_name": "Banyuwangi",
            "nama_pml": "Siti Aminah",
            "jumlah_sls": 3,
            "total_target": 120,
            "processed_count": 40,
            "remaining_count": 80,
            "open_count": 60,
            "draft_count": 20,
            "rejected_count": 2,
            "progress": 33.33,
        }
    )
    assert "Budi Santoso" in pcl_msg
    assert "33.33%" in pcl_msg
    assert "20 dokumen masih berstatus DRAFT" in pcl_msg

    pml_msg = build_pml_reminder_message(
        {
            "nama_pml": "Siti Aminah",
            "kec_name": "Banyuwangi",
            "jumlah_pcl": 4,
            "jumlah_sls": 12,
            "total_target": 500,
            "processed_count": 300,
            "remaining_count": 200,
            "approved_count": 250,
            "draft_count": 30,
            "progress": 60.0,
        }
    )
    assert "Siti Aminah" in pml_msg
    assert "50 usaha" in pml_msg

    broadcast = build_kecamatan_broadcast_message(
        "Kecamatan Banyuwangi (160)",
        [
            {
                "nama_pcl": "Budi Santoso",
                "nama_pml": "Siti Aminah",
                "total_target": 120,
                "processed_count": 40,
                "remaining_count": 80,
                "draft_count": 20,
                "progress": 33.33,
            }
        ],
    )
    assert "REKAP MONITORING SE2026" in broadcast
    assert "Budi Santoso" in broadcast


def test_register_admin_and_user_roles():
    from app import create_app
    from config import Config
    from models.user import User

    class TestCfg(Config):
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_ENGINE_OPTIONS = {}
        TESTING = True

    app = create_app(TestCfg)
    client = app.test_client()

    # Pastikan akses dashboard tanpa login diarahkan ke /login
    resp_unauth = client.get("/dashboard")
    assert resp_unauth.status_code == 302
    assert "/login" in resp_unauth.headers.get("Location", "")

    # Registrasi sebagai Admin
    res_admin = client.post(
        "/register",
        data={
            "nama_lengkap": "Admin Baru",
            "username": "admin_baru",
            "email": "admin_baru@bps.go.id",
            "role": "admin",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert res_admin.status_code == 302

    # Registrasi sebagai User
    res_user = client.post(
        "/register",
        data={
            "nama_lengkap": "User Baru",
            "username": "user_baru",
            "email": "user_baru@bps.go.id",
            "role": "user",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    assert res_user.status_code == 302

    with app.app_context():
        u_admin = User.query.filter_by(username="admin_baru").first()
        u_user = User.query.filter_by(username="user_baru").first()
        assert u_admin is not None and u_admin.role == "admin"
        assert u_user is not None and u_user.role == "user"

