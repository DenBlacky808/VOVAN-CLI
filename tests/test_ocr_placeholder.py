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
    list_completed = Mock(returncode=0, stdout='List of available languages in "/tmp":\neng\nrus\n', stderr="")
    ocr_completed = Mock(returncode=0, stdout="recognized text\n", stderr="")
    run_mock = Mock(side_effect=[list_completed, ocr_completed])
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    result = run_ocr(str(image), "tesseract", tesseract_lang="rus+eng")
    assert result["status"] == "completed"
    assert result["result_text"] == "recognized text"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "tesseract"
    assert run_mock.call_count == 2
    assert run_mock.call_args_list[1].args[0] == ["tesseract", str(image), "stdout", "-l", "rus+eng"]


def test_run_ocr_tesseract_missing_pdftoppm_for_pdf_falls_back(monkeypatch) -> None:
    monkeypatch.setattr(
        ocr_module.shutil,
        "which",
        lambda name: "/usr/bin/tesseract" if name == "tesseract" else None,
    )

    result = run_ocr("/tmp/demo.pdf", "tesseract")
    assert result["status"] == "completed"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "placeholder"
    assert "pdftoppm is not installed" in result["engine_warning"]


def test_pdf_conversion_command_built_correctly_and_page_ocr_called(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        ocr_module.shutil,
        "which",
        lambda name: f"/usr/bin/{name}" if name in {"tesseract", "pdftoppm"} else None,
    )

    page1 = tmp_path / "page-1.png"
    page2 = tmp_path / "page-2.png"
    page1.write_bytes(b"1")
    page2.write_bytes(b"2")

    captured = {}

    def fake_convert(self, pdf_path: Path, output_dir: Path):
        captured["pdf_path"] = pdf_path
        captured["output_dir"] = output_dir
        return [page1, page2]

    monkeypatch.setattr(ocr_module.PdftoppmPreprocessor, "convert_pdf_to_images", fake_convert)

    ocr_calls: list[str] = []

    def fake_run_tesseract(path: str, lang: str = "eng") -> dict:
        ocr_calls.append(path)
        return {
            "status": "completed",
            "result_text": f"text:{Path(path).name}",
            "source_file": path,
            "engine": "tesseract",
            "created_at": "x",
        }

    monkeypatch.setattr(ocr_module, "run_tesseract_ocr", fake_run_tesseract)

    result = run_ocr(str(pdf), "tesseract", tesseract_lang="rus+eng", pdf_max_pages=2, pdf_dpi=300)
    assert result["status"] == "completed"
    assert "--- PAGE 1 ---" in result["result_text"]
    assert "--- PAGE 2 ---" in result["result_text"]
    assert ocr_calls == [str(page1), str(page2)]
    assert captured["pdf_path"] == pdf


def test_pdftoppm_command_and_max_pages_respected(monkeypatch, tmp_path: Path) -> None:
    preprocessor = ocr_module.PdftoppmPreprocessor(dpi=200, max_pages=3)
    run_calls = []

    def fake_run(cmd, capture_output, text, check):
        run_calls.append(cmd)
        (tmp_path / "page-1.png").write_bytes(b"1")
        return Mock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(ocr_module.subprocess, "run", fake_run)
    pages = preprocessor.convert_pdf_to_images(tmp_path / "in.pdf", tmp_path)
    assert pages == [tmp_path / "page-1.png"]
    assert run_calls[0] == [
        "pdftoppm",
        "-f",
        "1",
        "-l",
        "3",
        "-r",
        "200",
        "-png",
        str(tmp_path / "in.pdf"),
        str(tmp_path / "page"),
    ]


def test_run_ocr_tesseract_missing_requested_language_falls_back_safely(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: "/usr/bin/tesseract")
    list_completed = Mock(returncode=0, stdout='List of available languages in "/tmp":\neng\n', stderr="")
    run_mock = Mock(return_value=list_completed)
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    result = run_ocr(str(image), "tesseract", tesseract_lang="rus+eng")
    assert result["status"] == "completed"
    assert result["engine"] == "placeholder"
    assert result["engine_requested"] == "tesseract"
    assert "not installed" in result["engine_warning"]
