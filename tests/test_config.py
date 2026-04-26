from pathlib import Path

from vovan.config import Settings, load_settings, validate_required_env


def test_validate_required_env_missing() -> None:
    settings = Settings(
        vladcher_base_url="",
        worker_token="",
        mode="local",
        data_dir=Path('.'),
        log_dir=Path('.'),
        report_dir=Path('.'),
        download_dir=Path('./data/downloads'),
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        dry_run=True,
        request_timeout_seconds=30,
        worker_sleep_seconds=5,
    )
    missing = validate_required_env(settings)
    assert "VLADCHER_BASE_URL" in missing
    assert "VOVAN_WORKER_TOKEN" in missing


def test_load_settings_reads_new_worker_env(monkeypatch) -> None:
    monkeypatch.setenv("VLADCHER_BASE_URL", "https://example.test")
    monkeypatch.setenv("VOVAN_WORKER_TOKEN", "token")
    monkeypatch.setenv("VOVAN_REQUEST_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("VOVAN_WORKER_SLEEP_SECONDS", "7")
    monkeypatch.setenv("VOVAN_DOWNLOAD_DIR", "./tmp/downloads")

    settings = load_settings(env_file=".env.missing")

    assert settings.request_timeout_seconds == 45
    assert settings.worker_sleep_seconds == 7
    assert settings.download_dir == Path("./tmp/downloads")
