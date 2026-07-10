from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressResult:
    processed: int
    remaining: int
    progress: float
    status: str
    warning: str | None = None


def calculate_progress(total_target, open_count, draft_count) -> ProgressResult:
    total = max(int(total_target or 0), 0)
    opened = max(int(open_count or 0), 0)
    draft = max(int(draft_count or 0), 0)
    warning = None
    if opened + draft > total:
        processed = 0
        warning = "OPEN + DRAFT melebihi total; processed_count ditetapkan menjadi 0."
    else:
        processed = min(max(total - opened - draft, 0), total)
    remaining = max(total - processed, 0)
    progress = round(processed / total * 100, 2) if total > 0 else 0.0
    if total == 0:
        status = "Data Kosong"
    elif processed == 0:
        status = "Belum Mulai"
    elif processed >= total:
        status = "Selesai"
    else:
        status = "Sedang Proses"
    return ProgressResult(processed, remaining, progress, status, warning)


def aggregate_progress(total: int, processed: int) -> float:
    return round(processed / total * 100, 2) if total else 0.0

