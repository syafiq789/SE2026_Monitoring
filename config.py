import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


# =========================================================
# Folder utama project
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# override=True agar nilai terbaru dari .env selalu digunakan
load_dotenv(ENV_FILE, override=True)


def env_bool(name: str, default: bool = False) -> bool:
    """
    Membaca nilai boolean dari file .env.

    Contoh nilai yang dianggap True:
    true, 1, yes, on
    """
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
    }


def normalize_database_url(database_url: str) -> str:
    """
    Menyesuaikan format DATABASE_URL agar cocok dengan SQLAlchemy.
    """

    database_url = database_url.strip()

    # Beberapa layanan memakai mysql://
    if database_url.startswith("mysql://"):
        database_url = database_url.replace(
            "mysql://",
            "mysql+pymysql://",
            1,
        )

    # Format lama PostgreSQL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1,
        )

    return database_url


class Config:
    # =====================================================
    # Konfigurasi utama Flask
    # =====================================================
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "se2026-bps-banyuwangi-secret-key-local",
    ).strip()

    DEBUG = env_bool("DEBUG", False)

    # =====================================================
    # Konfigurasi database MySQL lokal
    # =====================================================
    DB_HOST = os.getenv(
        "DB_HOST",
        "127.0.0.1",
    ).strip()

    DB_PORT = os.getenv(
        "DB_PORT",
        "3306",
    ).strip()

    DB_NAME = os.getenv(
        "DB_NAME",
        "se2026_monitoring",
    ).strip()

    DB_USER = os.getenv(
        "DB_USER",
        "root",
    ).strip()

    DB_PASSWORD = os.getenv(
        "DB_PASSWORD",
        "",
    )

    encoded_user = quote_plus(DB_USER)
    encoded_password = quote_plus(DB_PASSWORD)

    DEFAULT_DATABASE_URL = (
        f"mysql+pymysql://{encoded_user}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )

    DATABASE_URL = normalize_database_url(
        os.getenv(
            "DATABASE_URL",
            DEFAULT_DATABASE_URL,
        )
    )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =====================================================
    # Pengaturan koneksi database
    # =====================================================
    if DATABASE_URL.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {}
    elif DATABASE_URL.startswith(
        (
            "mysql://",
            "mysql+pymysql://",
        )
    ):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 280,
            "pool_timeout": 30,
            "connect_args": {
                "connect_timeout": 10,
            },
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 280,
            "pool_timeout": 30,
        }

    # Dipertahankan karena extensions.py Anda kemungkinan
    # masih menggunakan nama konfigurasi ini.
    DATABASE_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS

    # =====================================================
    # Folder upload dan export
    # =====================================================
    UPLOAD_FOLDER = str(
        BASE_DIR / os.getenv(
            "UPLOAD_FOLDER",
            "uploads",
        )
    )

    EXPORT_FOLDER = str(
        BASE_DIR / os.getenv(
            "EXPORT_FOLDER",
            "exports",
        )
    )

    MAX_CONTENT_LENGTH = int(
        os.getenv(
            "MAX_CONTENT_LENGTH",
            str(32 * 1024 * 1024),
        )
    )

    # =====================================================
    # Konfigurasi session login Flask
    # =====================================================
    SESSION_COOKIE_NAME = os.getenv(
        "SESSION_COOKIE_NAME",
        "se2026_session",
    ).strip()

    SESSION_COOKIE_HTTPONLY = True

    # Untuk lokal harus False karena masih menggunakan HTTP.
    # Untuk deployment HTTPS ubah menjadi True melalui .env.
    SESSION_COOKIE_SECURE = env_bool(
        "SESSION_COOKIE_SECURE",
        False,
    )

    # Untuk localhost dan iframe Streamlit lokal gunakan Lax.
    SESSION_COOKIE_SAMESITE = os.getenv(
        "SESSION_COOKIE_SAMESITE",
        "Lax",
    ).strip()

    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_PATH = "/"

    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(
            os.getenv(
                "SESSION_LIFETIME_HOURS",
                "8",
            )
        )
    )

    # Refresh masa aktif session ketika pengguna membuka halaman.
    SESSION_REFRESH_EACH_REQUEST = True