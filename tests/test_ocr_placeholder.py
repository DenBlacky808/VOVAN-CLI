from pathlib import Path
from unittest.mock import Mock

import vovan.ocr as ocr_module
from vovan.ocr import run_ocr, run_placeholder_ocr


def test_ocr_placeholder_contract() -> None:
    result = run_placeholder_ocr("/tmp/demo.pdf")
    assert result["status"] == "completed"
    assert result["result_text"] == "placeholder OCR result"
    assert result["source_file"] == "/tmp/demo.pdf"
    assert result["engine"] == "placeholder"
    assert "created_at" in result


def test_run_ocr_unsupported_engine_falls_back_safely() -> None:
    result = run_ocr("/tmp/demo.pdf", "unsupported")
    assert result["status"] == "completed"
    assert result["engine"] == "placeholder"
    assert result["engine_requested"] == "unsupported"
    assert "engine_warning" in result


def test_run_ocr_tesseract_unavailable_falls_back_safely(monkeypatch) -> None:
    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: None)
    result = run_ocr("/tmp/demo.png", "tesseract")
    assert result["status"] == "completed"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "placeholder"
    assert "not installed" in result["engine_warning"]


def test_run_ocr_tesseract_available_for_image(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: "/usr/bin/tesseract")
    completed = Mock(returncode=0, stdout="recognized text\n", stderr="")
    run_mock = Mock(return_value=completed)
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    result = run_ocr(str(image), "tesseract")
    assert result["status"] == "completed"
    assert result["result_text"] == "recognized text"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "tesseract"
    run_mock.assert_called_once()


def test_run_ocr_tesseract_available_but_pdf_falls_back(monkeypatch) -> None:
    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: "/usr/bin/tesseract")
    run_mock = Mock()
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    result = run_ocr("/tmp/demo.pdf", "tesseract")
    assert result["status"] == "completed"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "placeholder"
    assert "unsupported for this file" in result["engine_warning"]
    run_mock.assert_not_called()
