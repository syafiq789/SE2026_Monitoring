from datetime import datetime

from extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Kecamatan(TimestampMixin, db.Model):
    __tablename__ = "kecamatan"
    __table_args__ = (
        db.UniqueConstraint("prov_code", "kab_code", "kec_code", name="uq_kecamatan_wilayah"),
    )

    id = db.Column(db.Integer, primary_key=True)
    prov_code = db.Column(db.String(2), nullable=False)
    kab_code = db.Column(db.String(2), nullable=False)
    kec_code = db.Column(db.String(3), nullable=False, index=True)
    kec_name = db.Column(db.String(150), nullable=False, index=True)


class PML(TimestampMixin, db.Model):
    __tablename__ = "pml"
    __table_args__ = (
        db.UniqueConstraint("kecamatan_id", "email_pml", "nama_pml", name="uq_pml_wilayah_identitas"),
    )

    id = db.Column(db.Integer, primary_key=True)
    kecamatan_id = db.Column(
        db.Integer, db.ForeignKey("kecamatan.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    email_pml = db.Column(db.String(150), nullable=False, default="")
    nama_pml = db.Column(db.String(150), nullable=False, index=True)
    kecamatan = db.relationship("Kecamatan", backref=db.backref("pml_list", cascade="all, delete-orphan"))


class PCL(TimestampMixin, db.Model):
    __tablename__ = "pcl"
    __table_args__ = (
        db.UniqueConstraint(
            "kecamatan_id", "pml_id", "email_pcl", "username_pcl", "nama_pcl", name="uq_pcl_wilayah_identitas"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    kecamatan_id = db.Column(
        db.Integer, db.ForeignKey("kecamatan.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    pml_id = db.Column(
        db.Integer, db.ForeignKey("pml.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    email_pcl = db.Column(db.String(150), nullable=False, default="")
    username_pcl = db.Column(db.String(100), nullable=False, default="")
    nama_pcl = db.Column(db.String(150), nullable=False, index=True)
    kecamatan = db.relationship("Kecamatan", backref=db.backref("pcl_list", cascade="all, delete-orphan"))
    pml = db.relationship("PML", backref=db.backref("pcl_list", cascade="all, delete-orphan"))


class SLS(TimestampMixin, db.Model):
    __tablename__ = "sls"

    id = db.Column(db.BigInteger, primary_key=True)
    kecamatan_id = db.Column(
        db.Integer, db.ForeignKey("kecamatan.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    pml_id = db.Column(
        db.Integer, db.ForeignKey("pml.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    pcl_id = db.Column(
        db.Integer, db.ForeignKey("pcl.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    prov_code = db.Column(db.String(2), nullable=False)
    kab_code = db.Column(db.String(2), nullable=False)
    desa_code = db.Column(db.String(3), nullable=False, index=True)
    desa_name = db.Column(db.String(150), nullable=False)
    subsls_code = db.Column(db.String(6), nullable=False, index=True)
    subsls_name = db.Column(db.String(200), nullable=False)
    sls_key = db.Column(db.String(50), nullable=False, unique=True, index=True)

    approved_by_pengawas = db.Column(db.Integer, nullable=False, default=0)
    completed_by_admin_kabupaten = db.Column(db.Integer, nullable=False, default=0)
    draft_count = db.Column(db.Integer, nullable=False, default=0)
    edited_by_admin_kabupaten = db.Column(db.Integer, nullable=False, default=0)
    edited_by_pengawas = db.Column(db.Integer, nullable=False, default=0)
    open_count = db.Column(db.Integer, nullable=False, default=0)
    rejected_by_admin_kabupaten = db.Column(db.Integer, nullable=False, default=0)
    rejected_by_pengawas = db.Column(db.Integer, nullable=False, default=0)
    revoked_by_admin_kabupaten = db.Column(db.Integer, nullable=False, default=0)
    revoked_by_pengawas = db.Column(db.Integer, nullable=False, default=0)
    submitted_by_pencacah = db.Column(db.Integer, nullable=False, default=0)
    submitted_respondent = db.Column(db.Integer, nullable=False, default=0)
    total_target = db.Column(db.Integer, nullable=False, default=0)
    processed_count = db.Column(db.Integer, nullable=False, default=0)
    remaining_count = db.Column(db.Integer, nullable=False, default=0)
    progress = db.Column(db.Numeric(6, 2), nullable=False, default=0)
    progress_status = db.Column(db.String(30), nullable=False, index=True)

    kecamatan = db.relationship("Kecamatan", backref=db.backref("sls_list", cascade="all, delete-orphan"))
    pml = db.relationship("PML", backref=db.backref("sls_list", cascade="all, delete-orphan"))
    pcl = db.relationship("PCL", backref=db.backref("sls_list", cascade="all, delete-orphan"))

