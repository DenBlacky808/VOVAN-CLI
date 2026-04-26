from pathlib import Path
from unittest.mock import Mock

from vovan.cli import cmd_doctor
from vovan.config import Settings


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        vladcher_base_url="https://worker.example",
        worker_token="token",
        mode="local",
        data_dir=tmp_path / "data",
        log_dir=tmp_path / "logs",
        report_dir=tmp_path / "reports",
        allowed_extensions={".txt"},
        max_file_size_mb=1,
        dry_run=True,
        ocr_engine="placeholder",
        tesseract_lang="rus+eng",
    )


def test_cmd_doctor_reports_tesseract_fields(monkeypatch, tmp_path: Path, capsys) -> None:
    from vovan import cli as cli_module
    from vovan import ocr as ocr_module

    monkeypatch.setattr(cli_module, "load_settings", lambda: _settings(tmp_path))
    monkeypatch.setattr(cli_module, "write_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: "/usr/local/bin/tesseract")
    run_mock = Mock(return_value=Mock(returncode=0, stdout="List of available languages in /tmp:\neng\nrus\n", stderr=""))
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    exit_code = cmd_doctor()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"tesseract_available": true' in output
    assert '"tesseract_path": "/usr/local/bin/tesseract"' in output
    assert '"tesseract_languages_available": [' in output
    assert '"tesseract_lang_configured": "rus+eng"' in output
    assert '"tesseract_lang_available": true' in output
