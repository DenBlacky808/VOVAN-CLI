import json
from pathlib import Path
from unittest.mock import Mock

from vovan.cli import cmd_doctor
from vovan.config import Settings


def _settings() -> Settings:
    return Settings(
        vladcher_base_url="https://worker.example",
        worker_token="token",
        mode="local",
        data_dir=Path("./data"),
        log_dir=Path("./logs"),
        report_dir=Path("./reports"),
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        dry_run=True,
        ocr_engine="placeholder",
        tesseract_lang="rus+eng",
    )


def test_cmd_doctor_reports_tesseract_fields(monkeypatch, capsys) -> None:
    from vovan import cli as cli_module

    monkeypatch.setattr(cli_module, "load_settings", _settings)
    monkeypatch.setattr(cli_module, "validate_required_env", lambda _: [])
    monkeypatch.setattr(cli_module, "get_tesseract_path", lambda: "/usr/bin/tesseract")
    monkeypatch.setattr(cli_module, "list_tesseract_languages", lambda: ["eng", "rus"])
    monkeypatch.setattr(cli_module, "write_report", Mock())

    exit_code = cmd_doctor()
    assert exit_code == 0

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["tesseract_available"] is True
    assert payload["tesseract_path"] == "/usr/bin/tesseract"
    assert payload["tesseract_languages_available"] == ["eng", "rus"]
    assert payload["tesseract_lang_configured"] == "rus+eng"
    assert payload["tesseract_lang_available"] is True
