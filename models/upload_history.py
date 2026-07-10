from datetime import datetime

from extensions import db


class UploadHistory(db.Model):
    __tablename__ = "upload_history"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    processed_sheet = db.Column(db.String(100))
    file_type = db.Column(db.String(10), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False, default=0)
    source_rows = db.Column(db.Integer, nullable=False, default=0)
    imported_rows = db.Column(db.Integer, nullable=False, default=0)
    skipped_rows = db.Column(db.Integer, nullable=False, default=0)
    duplicate_rows = db.Column(db.Integer, nullable=False, default=0)
    warning_count = db.Column(db.Integer, nullable=False, default=0)
    total_kecamatan = db.Column(db.Integer, nullable=False, default=0)
    total_pml = db.Column(db.Integer, nullable=False, default=0)
    total_pcl = db.Column(db.Integer, nullable=False, default=0)
    total_sls = db.Column(db.Integer, nullable=False, default=0)
    total_target = db.Column(db.BigInteger, nullable=False, default=0)
    total_processed = db.Column(db.BigInteger, nullable=False, default=0)
    total_remaining = db.Column(db.BigInteger, nullable=False, default=0)
    progress = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    status = db.Column(db.Enum("processing", "success", "failed", name="upload_status"), nullable=False)
    message = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    user = db.relationship("User", backref=db.backref("upload_history", lazy="dynamic"))

