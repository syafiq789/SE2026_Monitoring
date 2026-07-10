from utils.column_mapper import canonical_column_name, normalize_column_name


def test_normalize_column_name():
    assert normalize_column_name(" APPROVED.BY.Pengawas\n") == "approved_by_pengawas"
    assert normalize_column_name("email PML") == "email_pml"


def test_column_aliases():
    assert canonical_column_name("email") == "email_pcl"
    assert canonical_column_name("username") == "username_pcl"
    assert canonical_column_name("DRAFT") == "draft_count"
    assert canonical_column_name("OPEN") == "open_count"
    assert canonical_column_name("total") == "total_target"
    assert canonical_column_name("PCL") == "nama_pcl"
    assert canonical_column_name("PML") == "nama_pml"

