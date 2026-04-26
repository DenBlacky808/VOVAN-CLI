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
        tesseract_lang="rus+eng",
    )


def test_doctor_reports_tesseract_availability_and_languages(monkeypatch, capsys) -> None:
    from vovan import cli as cli_module

    monkeypatch.setattr(cli_module, "load_settings", _settings)
    monkeypatch.setattr(cli_module, "validate_required_env", lambda _: [])
    monkeypatch.setattr(cli_module, "write_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli_module, "_is_tesseract_available", lambda: True)
    monkeypatch.setattr(cli_module, "list_tesseract_languages", lambda: ["eng", "rus"])

    which_mock = Mock(return_value="/usr/local/bin/tesseract")
    monkeypatch.setattr("shutil.which", which_mock)

    exit_code = cmd_doctor()
    out = capsys.readouterr().out
    result = json.loads(out)

    assert exit_code == 0
    assert result["tesseract_available"] is True
    assert result["tesseract_path"] == "/usr/local/bin/tesseract"
    assert result["tesseract_languages_available"] == ["eng", "rus"]
    assert result["tesseract_lang_configured"] == "rus+eng"
    assert result["tesseract_lang_available"] is True
