from pathlib import Path

from vovan.config import Settings, validate_required_env


def test_validate_required_env_missing() -> None:
    settings = Settings(
        vladcher_base_url="",
        worker_token="",
        mode="local",
        data_dir=Path("."),
        log_dir=Path("."),
        report_dir=Path("."),
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        dry_run=True,
        request_timeout_seconds=30,
        worker_sleep_seconds=5,
        download_dir=Path("./data/downloads"),
    )
    missing = validate_required_env(settings)
    assert "VLADCHER_BASE_URL" in missing
    assert "VOVAN_WORKER_TOKEN" in missing
