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


def test_settings_default_tesseract_lang() -> None:
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
    assert settings.tesseract_lang == "eng"


def test_load_settings_reads_tesseract_lang_from_env_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VOVAN_TESSERACT_LANG", raising=False)
    env_file = tmp_path / ".env.test"
    env_file.write_text("VOVAN_TESSERACT_LANG=rus+eng\n", encoding="utf-8")

    settings = load_settings(str(env_file))
    assert settings.tesseract_lang == "rus+eng"


def test_settings_default_pdf_processing_values() -> None:
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
    assert settings.pdf_max_pages == 3
    assert settings.pdf_dpi == 200


def test_load_settings_reads_pdf_settings_from_env_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VOVAN_PDF_MAX_PAGES", raising=False)
    monkeypatch.delenv("VOVAN_PDF_DPI", raising=False)
    env_file = tmp_path / ".env.test"
    env_file.write_text("VOVAN_PDF_MAX_PAGES=5\nVOVAN_PDF_DPI=300\n", encoding="utf-8")

    settings = load_settings(str(env_file))
    assert settings.pdf_max_pages == 5
    assert settings.pdf_dpi == 300


def test_settings_default_worker_poll_values() -> None:
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
    assert settings.worker_poll_seconds == 5.0
    assert settings.worker_error_backoff_seconds == 15.0


def test_load_settings_reads_worker_poll_settings_from_env_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VOVAN_WORKER_POLL_SECONDS", raising=False)
    monkeypatch.delenv("VOVAN_WORKER_ERROR_BACKOFF_SECONDS", raising=False)
    env_file = tmp_path / ".env.test"
    env_file.write_text(
        "VOVAN_WORKER_POLL_SECONDS=2\nVOVAN_WORKER_ERROR_BACKOFF_SECONDS=8\n",
        encoding="utf-8",
    )

    settings = load_settings(str(env_file))
    assert settings.worker_poll_seconds == 2.0
    assert settings.worker_error_backoff_seconds == 8.0
