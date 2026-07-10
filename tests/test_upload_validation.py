import pandas as pd
import pytest

from services.upload_service import prepare_import_data
from utils.validators import ImportValidationError


def valid_row(**overrides):
    row = {
        "prov": "35", "kab": "10", "kec_code": "010", "kec_name": "Kecamatan A",
        "desa_code": "001", "desa_name": "Desa A", "subsls_code": "000100",
        "subsls_name": "SLS A", "email": "pcl@example.test", "username": "pcl01",
        "APPROVED.BY.Pengawas": "40", "DRAFT": "10", "OPEN": "20", "total": "100",
        "email PML": "pml@example.test", "PCL": "Pencacah A", "PML": "Pengawas A",
        "Unnamed: 26": "",
    }
    row.update(overrides)
    return row


def test_excel_finds_sls_ignores_pivot_and_keeps_leading_zero(tmp_path):
    path = tmp_path / "contoh.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"hasil": ["pivot"]}).to_excel(writer, sheet_name="Pivot Table PML", index=False)
        pd.DataFrame([valid_row()]).to_excel(writer, sheet_name="  SLS  ", index=False)
    prepared = prepare_import_data(path)
    assert prepared["processed_sheet"] == "  SLS  "
    assert len(prepared["records"]) == 1
    record = prepared["records"][0]
    assert record["kec_code"] == "010"
    assert record["desa_code"] == "001"
    assert record["subsls_code"] == "000100"
    assert "unnamed_26" not in prepared["read_columns"]


def test_csv_is_read_directly(tmp_path):
    path = tmp_path / "sls.csv"
    pd.DataFrame([valid_row()]).to_csv(path, index=False, encoding="utf-8-sig")
    prepared = prepare_import_data(path)
    assert prepared["processed_sheet"] == "CSV"


def test_conflicting_duplicate_key_is_rejected(tmp_path):
    path = tmp_path / "duplicate.xlsx"
    rows = [valid_row(total="100"), valid_row(total="101")]
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="sls", index=False)
    with pytest.raises(ImportValidationError, match="ganda dengan nilai yang berbeda"):
        prepare_import_data(path)


def test_missing_required_column_explains_columns(tmp_path):
    path = tmp_path / "invalid.xlsx"
    row = valid_row()
    del row["PML"]
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([row]).to_excel(writer, sheet_name="sls", index=False)
    with pytest.raises(ImportValidationError) as error:
        prepare_import_data(path)
    assert "nama_pml" in error.value.missing_columns

