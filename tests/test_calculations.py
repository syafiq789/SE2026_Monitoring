import pytest

from utils.calculations import calculate_progress


@pytest.mark.parametrize(
    "total,opened,draft,processed,remaining,progress,status",
    [
        (460, 86, 55, 319, 141, 69.35, "Sedang Proses"),
        (341, 341, 0, 0, 341, 0, "Belum Mulai"),
        (100, 0, 0, 100, 0, 100, "Selesai"),
        (0, 0, 0, 0, 0, 0, "Data Kosong"),
    ],
)
def test_required_progress_cases(total, opened, draft, processed, remaining, progress, status):
    result = calculate_progress(total, opened, draft)
    assert result.processed == processed
    assert result.remaining == remaining
    assert result.progress == progress
    assert result.status == status


def test_open_plus_draft_above_total_is_safe():
    result = calculate_progress(10, 8, 5)
    assert result.processed == 0
    assert result.remaining == 10
    assert result.warning

