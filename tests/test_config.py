from pathlib import Path

from vovan.config import Settings, load_settings, validate_required_env


def test_validate_required_env_missing() -> None:
    settings = Settings(
        vladcher_base_url="",
        worker_token="",
        mode="local",
        data_dir=Path("./data"),
        log_dir=Path("./logs"),
        report_dir=Path("./reports"),
        download_dir=Path("./data/downloads"),
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        request_timeout_seconds=30,
        worker_sleep_seconds=5,
        dry_run=True,
    )
    missing = validate_required_env(settings)
    assert "VLADCHER_BASE_URL" in missing
    assert "VOVAN_WORKER_TOKEN" in missing


def test_load_settings_new_worker_env(monkeypatch) -> None:
    monkeypatch.setenv("VOVAN_REQUEST_TIMEOUT_SECONDS", "17")
    monkeypatch.setenv("VOVAN_WORKER_SLEEP_SECONDS", "9")
    monkeypatch.setenv("VOVAN_DOWNLOAD_DIR", "./data/new-downloads")
    settings = load_settings(env_file=".env.not.exists")
    assert settings.request_timeout_seconds == 17
    assert settings.worker_sleep_seconds == 9
    assert settings.download_dir == Path("./data/new-downloads")
