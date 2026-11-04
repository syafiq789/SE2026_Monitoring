import os
import shutil
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


# =========================================================
# Folder utama project
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
BUNDLED_SQLITE_DB = BASE_DIR / "se2026_bundled.db"
VERCEL_TMP_SQLITE_DB = Path("/tmp/se2026_monitoring.db")

# override=True agar nilai terbaru dari .env selalu digunakan
load_dotenv(ENV_FILE, override=True)


def ensure_vercel_sqlite_seeded() -> Path:
    """
    Menyalin database awal (se2026_bundled.db) ke /tmp/se2026_monitoring.db
    di Vercel apabila instance serverless baru belum memiliki file database.
    """
    try:
        if (
            BUNDLED_SQLITE_DB.exists()
            and (
                not VERCEL_TMP_SQLITE_DB.exists()
                or VERCEL_TMP_SQLITE_DB.stat().st_size < 100_000
            )
        ):
            VERCEL_TMP_SQLITE_DB.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BUNDLED_SQLITE_DB, VERCEL_TMP_SQLITE_DB)
    except Exception:
        pass
    return VERCEL_TMP_SQLITE_DB


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
    IS_VERCEL = bool(os.getenv("VERCEL"))

    # =====================================================
    # Konfigurasi database MySQL lokal / Cloud Vercel
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

    if IS_VERCEL and not os.getenv("DATABASE_URL") and DB_HOST in {"127.0.0.1", "localhost"}:
        ensure_vercel_sqlite_seeded()
        DEFAULT_DATABASE_URL = f"sqlite:///{VERCEL_TMP_SQLITE_DB.as_posix()}"
    else:
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

    DATABASE_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS

    # =====================================================
    # Folder upload dan export (Gunakan /tmp di Vercel)
    # =====================================================
    _STORAGE_ROOT = Path("/tmp") if IS_VERCEL else BASE_DIR

    UPLOAD_FOLDER = str(
        _STORAGE_ROOT / os.getenv(
            "UPLOAD_FOLDER",
            "uploads",
        )
    )

    EXPORT_FOLDER = str(
        _STORAGE_ROOT / os.getenv(
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

    SESSION_COOKIE_SECURE = env_bool(
        "SESSION_COOKIE_SECURE",
        False,
    )

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

    SESSION_REFRESH_EACH_REQUEST = True
    ALLOW_PUBLIC_REGISTER = env_bool("ALLOW_PUBLIC_REGISTER", True)
