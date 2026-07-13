import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE, override=True)


class Config:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "se2026-bps-banyuwangi-secret-key",
    )

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1").strip()
    DB_PORT = os.getenv("DB_PORT", "3306").strip()
    DB_NAME = os.getenv("DB_NAME", "se2026_monitoring").strip()
    DB_USER = os.getenv("DB_USER", "root").strip()
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    encoded_user = quote_plus(DB_USER)
    encoded_password = quote_plus(DB_PASSWORD)

    DEFAULT_DATABASE_URL = (
        f"mysql+pymysql://{encoded_user}:{encoded_password}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        DEFAULT_DATABASE_URL,
    ).strip()

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "connect_args": {
            "connect_timeout": 10,
        },
    }

    DATABASE_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS

    UPLOAD_FOLDER = str(BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads"))
    EXPORT_FOLDER = str(BASE_DIR / os.getenv("EXPORT_FOLDER", "exports"))

    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_CONTENT_LENGTH", str(32 * 1024 * 1024))
    )

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"