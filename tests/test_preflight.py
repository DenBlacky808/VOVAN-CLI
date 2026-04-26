from pathlib import Path

from vovan.config import Settings
from vovan.preflight import run_preflight


def test_preflight_txt_file(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")

    settings = Settings(
        vladcher_base_url="x",
        worker_token="y",
        mode="local",
        data_dir=tmp_path,
        log_dir=tmp_path,
        report_dir=tmp_path,
        allowed_extensions={".txt", ".pdf"},
        max_file_size_mb=1,
        dry_run=True,
        request_timeout_seconds=30,
        worker_sleep_seconds=5,
        download_dir=tmp_path / "downloads",
    )

    result = run_preflight(str(sample), settings)
    assert result["exists"] is True
    assert result["suitable_for_ocr"] is True
