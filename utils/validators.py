class ImportValidationError(ValueError):
    def __init__(self, message: str, read_columns=None, missing_columns=None):
        super().__init__(message)
        self.read_columns = sorted(read_columns or [])
        self.missing_columns = sorted(missing_columns or [])


def clean_text(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat", "<na>"}:
        return ""
    return " ".join(text.split())


def clean_code(value, width: int) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(char for char in text if char.isdigit())
    return digits.zfill(width) if digits else ""


def ensure_allowed_file(filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in {"xlsx", "csv"}:
        raise ImportValidationError("Format file tidak didukung. Gunakan file XLSX atau CSV.")
    return extension

