import re


COLUMN_ALIASES = {
    "prov": "prov",
    "kab": "kab",
    "kec_code": "kec_code",
    "kec_name": "kec_name",
    "desa_code": "desa_code",
    "desa_name": "desa_name",
    "subsls_code": "subsls_code",
    "subsls_name": "subsls_name",
    "email": "email_pcl",
    "username": "username_pcl",
    "approved_by_pengawas": "approved_by_pengawas",
    "completed_by_admin_kabupaten": "completed_by_admin_kabupaten",
    "draft": "draft_count",
    "draft_count": "draft_count",
    "edited_by_admin_kabupaten": "edited_by_admin_kabupaten",
    "edited_by_pengawas": "edited_by_pengawas",
    "open": "open_count",
    "open_count": "open_count",
    "rejected_by_admin_kabupaten": "rejected_by_admin_kabupaten",
    "rejected_by_pengawas": "rejected_by_pengawas",
    "revoked_by_admin_kabupaten": "revoked_by_admin_kabupaten",
    "revoked_by_pengawas": "revoked_by_pengawas",
    "submitted_by_pencacah": "submitted_by_pencacah",
    "submitted_respondent": "submitted_respondent",
    "total": "total_target",
    "total_target": "total_target",
    "email_pml": "email_pml",
    "pcl": "nama_pcl",
    "nama_pcl": "nama_pcl",
    "pml": "nama_pml",
    "nama_pml": "nama_pml",
}

REQUIRED_COLUMNS = {
    "kec_code",
    "kec_name",
    "desa_code",
    "desa_name",
    "subsls_code",
    "subsls_name",
    "nama_pcl",
    "nama_pml",
    "total_target",
    "open_count",
    "draft_count",
}

DETAIL_STATUS_COLUMNS = [
    "approved_by_pengawas",
    "completed_by_admin_kabupaten",
    "edited_by_admin_kabupaten",
    "edited_by_pengawas",
    "rejected_by_admin_kabupaten",
    "rejected_by_pengawas",
    "revoked_by_admin_kabupaten",
    "revoked_by_pengawas",
    "submitted_by_pencacah",
    "submitted_respondent",
]

NUMERIC_COLUMNS = DETAIL_STATUS_COLUMNS + ["draft_count", "open_count", "total_target"]


def normalize_column_name(value) -> str:
    name = str(value).strip().replace("\n", " ").replace("\r", " ").lower()
    name = name.replace(".", "_")
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    return re.sub(r"_+", "_", name).strip("_")


def canonical_column_name(value) -> str:
    normalized = normalize_column_name(value)
    return COLUMN_ALIASES.get(normalized, normalized)


def normalize_dataframe_columns(df):
    df = df.copy()
    df.columns = [canonical_column_name(column) for column in df.columns]
    return df

