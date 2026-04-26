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
        allowed_extensions={".txt", ".pdf"},
        max_file_size_mb=1,
        dry_run=True,
    )


def test_cmd_ocr_preserves_result_text_and_adds_analysis_fields(monkeypatch, capsys) -> None:
    from vovan import cli as cli_module

    monkeypatch.setattr(cli_module, "load_settings", _settings)
    monkeypatch.setattr(
        cli_module,
        "run_preflight",
        lambda *args, **kwargs: {"suitable_for_ocr": True},
    )
    monkeypatch.setattr(
        cli_module,
        "run_ocr",
        lambda *args, **kwargs: {
            "status": "completed",
            "result_text": "Общее собрание жильцов. Повестка дня.",
            "engine": "placeholder",
            "engine_requested": "placeholder",
        },
    )
    monkeypatch.setattr(cli_module, "write_report", lambda *args, **kwargs: None)

    exit_code = cmd_ocr("/tmp/fake.pdf")
    out = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert out["result_text"] == "Общее собрание жильцов. Повестка дня."
    assert out["engine"] == "placeholder"
    assert out["engine_requested"] == "placeholder"
    assert out["ocr_engine"] == "placeholder"

    assert "normalized_text" in out
    assert "document_type" in out
    assert "document_title" in out
    assert "short_summary" in out
    assert out["document_type"] == "meeting_notice"
