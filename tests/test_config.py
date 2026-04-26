from vovan.config import Settings, load_settings, validate_required_env


def test_validate_required_env_missing() -> None:
    settings = Settings(
        vladcher_base_url="",
        worker_token="",
        mode="local",
        data_dir=None,
        log_dir=None,
        report_dir=None,
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        dry_run=True,
    )
    missing = validate_required_env(settings)
    assert "VLADCHER_BASE_URL" in missing
    assert "VOVAN_WORKER_TOKEN" in missing


def test_load_settings_default_ocr_engine(monkeypatch) -> None:
    monkeypatch.delenv("VOVAN_OCR_ENGINE", raising=False)
    settings = load_settings(env_file="non-existent.env")
    assert settings.ocr_engine == "placeholder"
