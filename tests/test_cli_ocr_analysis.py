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
        max_file_size_mb=1,
        dry_run=True,
    )


def test_cmd_ocr_preserves_result_text_and_adds_analysis_fields(monkeypatch, capsys) -> None:
    from vovan import cli as cli_module

    monkeypatch.setattr(cli_module, "load_settings", _settings)
    monkeypatch.setattr(cli_module, "run_preflight", lambda path, settings: {"suitable_for_ocr": True})
    monkeypatch.setattr(
        cli_module,
        "run_ocr",
        lambda *args, **kwargs: {
            "status": "completed",
            "result_text": "RAW OCR",
            "engine": "placeholder",
            "engine_requested": "placeholder",
            "ocr_engine": "placeholder",
            "normalized_text": "RAW OCR",
            "document_type": "unknown",
            "document_title": "RAW OCR",
            "short_summary": "Тип: unknown. RAW OCR",
        },
    )
    monkeypatch.setattr(cli_module, "write_report", lambda *args, **kwargs: None)

    code = cmd_ocr("/tmp/doc.pdf")
    assert code == 0

    out = json.loads(capsys.readouterr().out)
    assert out["result_text"] == "RAW OCR"
    assert out["engine"] == "placeholder"
    assert out["engine_requested"] == "placeholder"
    assert out["ocr_engine"] == "placeholder"
    assert out["normalized_text"] == "RAW OCR"
    assert out["document_type"] == "unknown"
    assert out["document_title"] == "RAW OCR"
    assert "short_summary" in out
