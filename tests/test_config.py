from pathlib import Path

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


def test_settings_default_ocr_engine() -> None:
    settings = Settings(
        vladcher_base_url="x",
        worker_token="y",
        mode="local",
        data_dir=None,
        log_dir=None,
        report_dir=None,
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        dry_run=True,
    )
    assert settings.ocr_engine == "placeholder"
    assert settings.tesseract_lang == "eng"


def test_load_settings_tesseract_lang_defaults_to_eng(tmp_path: Path) -> None:
    settings = load_settings(env_file=str(tmp_path / ".env.missing"))
    assert settings.tesseract_lang == "eng"


def test_load_settings_reads_tesseract_lang(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VOVAN_TESSERACT_LANG", "rus+eng")
    settings = load_settings(env_file=str(tmp_path / ".env.missing"))
    assert settings.tesseract_lang == "rus+eng"
