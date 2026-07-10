from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app


def local_now():
    return datetime.now(ZoneInfo(current_app.config.get("APP_TIMEZONE", "Asia/Jakarta")))


def export_timestamp() -> str:
    return local_now().strftime("%Y%m%d_%H%M%S")


def filters_from_request(args) -> dict:
    return {
        "kec_code": args.get("kec_code", "").strip(),
        "desa_code": args.get("desa_code", "").strip(),
        "pml_id": args.get("pml_id", type=int),
        "pcl_id": args.get("pcl_id", type=int),
        "status": args.get("status", "").strip(),
        "progress_min": args.get("progress_min", type=float),
        "progress_max": args.get("progress_max", type=float),
    }

