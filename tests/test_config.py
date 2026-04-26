from pathlib import Path

from vovan.config import Settings, load_settings, validate_required_env


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


def test_load_settings_new_env(tmp_path: Path, monkeypatch) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "\n".join(
            [
                "VLADCHER_BASE_URL=https://api.example",
                "VOVAN_WORKER_TOKEN=abc",
                "VOVAN_REQUEST_TIMEOUT_SECONDS=11",
                "VOVAN_WORKER_SLEEP_SECONDS=9",
                "VOVAN_DOWNLOAD_DIR=./tmp/downloads",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("VOVAN_REQUEST_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("VOVAN_WORKER_SLEEP_SECONDS", raising=False)
    monkeypatch.delenv("VOVAN_DOWNLOAD_DIR", raising=False)

    settings = load_settings(str(env))
    assert settings.request_timeout_seconds == 11
    assert settings.worker_sleep_seconds == 9
    assert str(settings.download_dir) == "tmp/downloads"
