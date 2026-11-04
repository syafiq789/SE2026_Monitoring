import logging
from extensions import db
from models.activity_log import ActivityLog

logger = logging.getLogger(__name__)


def log_activity(user_id=None, action="", target="", details="", ip_address=None):
    """
    Mencatat log aktivitas pengguna ke database secara aman (fail-safe).
    Jika terjadi kesalahan koneksi atau tabel belum dibuat, aplikasi tetap berjalan lancar.
    """
    try:
        log = ActivityLog(
            user_id=user_id,
            action=action.upper(),
            target=str(target)[:100] if target else None,
            ip_address=ip_address,
            details=str(details) if details else None,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning("Gagal menyimpan activity log: %s", e)


def get_activity_logs(limit=200, action_filter=None, search=None):
    """
    Mengambil data riwayat aktivitas untuk tampilan audit trail Admin.
    """
    try:
        query = ActivityLog.query.order_by(ActivityLog.created_at.desc())

        if action_filter:
            query = query.filter(ActivityLog.action == action_filter.upper())

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (ActivityLog.details.ilike(search_term))
                | (ActivityLog.target.ilike(search_term))
                | (ActivityLog.action.ilike(search_term))
            )

        return query.limit(limit).all()
    except Exception as e:
        logger.warning("Gagal mengambil activity log: %s", e)
        return []
