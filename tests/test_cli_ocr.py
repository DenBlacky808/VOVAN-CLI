import json
from pathlib import Path

from vovan.cli import cmd_ocr
from vovan.config import Settings


def _settings() -> Settings:
    return Settings(
        vladcher_base_url="https://worker.example",
        worker_token="token",
        mode="local",
        data_dir=Path("./data"),
        log_dir=Path("./logs"),
        report_dir=Path("./reports"),
        allowed_extensions={".pdf"},
        max_file_size_mb=5,
        dry_run=True,
    )


def test_cli_ocr_output_preserves_result_text_and_adds_analysis_fields(monkeypatch, capsys) -> None:
    from vovan import cli as cli_module

    monkeypatch.setattr(cli_module, "load_settings", _settings)
    monkeypatch.setattr(
        cli_module,
        "run_preflight",
        lambda path, settings: {"suitable_for_ocr": True, "path": path},
    )
    monkeypatch.setattr(
        cli_module,
        "run_ocr",
        lambda *args, **kwargs: {
            "status": "completed",
            "result_text": "Общее   собрание\nПовестка",
            "engine": "tesseract",
            "engine_requested": "tesseract",
        },
    )
    monkeypatch.setattr(cli_module, "write_report", lambda *args, **kwargs: None)

    exit_code = cmd_ocr("/tmp/input.pdf")
    out = capsys.readouterr().out
    result = json.loads(out)

    assert exit_code == 0
    assert result["result_text"] == "Общее   собрание\nПовестка"
    assert result["engine"] == "tesseract"
    assert result["engine_requested"] == "tesseract"
    assert result["ocr_engine"] == "tesseract"

    assert "normalized_text" in result
    assert result["normalized_text"] == "Общее собрание Повестка"
    assert result["document_type"] == "meeting_notice"
    assert "document_title" in result
    assert "short_summary" in result
