from __future__ import annotations

from subprocess import CompletedProcess

from vovan.ocr import run_ocr, run_placeholder_ocr


def test_ocr_placeholder_contract() -> None:
    result = run_placeholder_ocr("/tmp/demo.pdf")
    assert result["status"] == "completed"
    assert result["result_text"] == "placeholder OCR result"
    assert result["source_file"] == "/tmp/demo.pdf"
    assert result["engine"] == "placeholder"
    assert "created_at" in result


def test_run_ocr_placeholder_is_default() -> None:
    result = run_ocr("/tmp/demo.pdf")
    assert result["status"] == "completed"
    assert result["engine"] == "placeholder"
    assert result["engine_requested"] == "placeholder"


def test_run_ocr_unsupported_engine_falls_back_safely() -> None:
    result = run_ocr("/tmp/demo.pdf", "unsupported")
    assert result["status"] == "completed"
    assert result["engine"] == "placeholder"
    assert result["engine_requested"] == "unsupported"
    assert "engine_warning" in result


def test_run_ocr_tesseract_unavailable_falls_back_safely(monkeypatch) -> None:
    monkeypatch.setattr("vovan.ocr.shutil.which", lambda _: None)

    result = run_ocr("/tmp/demo.pdf", "tesseract")
    assert result["status"] == "completed"
    assert result["engine"] == "placeholder"
    assert result["engine_requested"] == "tesseract"
    assert "binary not found" in result["engine_warning"]


def test_run_ocr_tesseract_available_uses_adapter(monkeypatch) -> None:
    monkeypatch.setattr("vovan.ocr.shutil.which", lambda _: "/usr/bin/tesseract")

    def fake_run(*args, **kwargs):
        return CompletedProcess(args=args[0], returncode=0, stdout="hello from tess", stderr="")

    monkeypatch.setattr("vovan.ocr.subprocess.run", fake_run)

    result = run_ocr("/tmp/demo.png", "tesseract")
    assert result["status"] == "completed"
    assert result["engine"] == "tesseract"
    assert result["engine_requested"] == "tesseract"
    assert result["result_text"] == "hello from tess"


def test_run_ocr_tesseract_available_but_empty_output_falls_back(monkeypatch) -> None:
    monkeypatch.setattr("vovan.ocr.shutil.which", lambda _: "/usr/bin/tesseract")

    def fake_run(*args, **kwargs):
        return CompletedProcess(args=args[0], returncode=0, stdout="\n", stderr="")

    monkeypatch.setattr("vovan.ocr.subprocess.run", fake_run)

    result = run_ocr("/tmp/demo.png", "tesseract")
    assert result["status"] == "completed"
    assert result["engine"] == "placeholder"
    assert result["engine_requested"] == "tesseract"
    assert "Fallback to placeholder" in result["engine_warning"]
