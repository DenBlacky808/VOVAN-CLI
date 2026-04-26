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


def test_run_ocr_tesseract_available_but_pdf_without_pdftoppm_falls_back(monkeypatch) -> None:
    def which(binary: str):
        if binary == "tesseract":
            return "/usr/bin/tesseract"
        return None

    monkeypatch.setattr(ocr_module.shutil, "which", which)
    monkeypatch.setattr(ocr_module, "list_tesseract_languages", lambda: ["eng"])

    result = run_ocr("/tmp/demo.pdf", "tesseract")
    assert result["status"] == "completed"
    assert result["engine_requested"] == "tesseract"
    assert result["engine"] == "placeholder"
    assert "pdftoppm" in result["engine_warning"]


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


def test_pdf_conversion_command_is_built_correctly(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF")

    page1 = tmp_path / "page-1.png"
    page2 = tmp_path / "page-2.png"
    page1.write_bytes(b"img1")
    page2.write_bytes(b"img2")

    class TempDirStub:
        def __enter__(self):
            return str(tmp_path)

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(ocr_module, "tempfile", ocr_module.tempfile)
    monkeypatch.setattr(ocr_module.tempfile, "TemporaryDirectory", lambda prefix: TempDirStub())
    monkeypatch.setattr(ocr_module.shutil, "which", lambda b: "/usr/bin/pdftoppm" if b == "pdftoppm" else None)

    completed = Mock(returncode=0, stdout="", stderr="")
    run_mock = Mock(return_value=completed)
    monkeypatch.setattr(ocr_module.subprocess, "run", run_mock)

    images = ocr_module._convert_pdf_to_images(pdf, pdf_max_pages=3, pdf_dpi=200)
    assert len(images) == 2
    assert run_mock.call_args.args[0] == [
        "pdftoppm",
        "-png",
        "-r",
        "200",
        "-f",
        "1",
        "-l",
        "3",
        str(pdf),
        str(tmp_path / "page"),
    ]

    for image in images:
        image.unlink(missing_ok=True)


def test_pdf_max_pages_limit_is_respected(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF")

    for idx in range(1, 6):
        (tmp_path / f"page-{idx}.png").write_bytes(f"img{idx}".encode())

    class TempDirStub:
        def __enter__(self):
            return str(tmp_path)

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(ocr_module.tempfile, "TemporaryDirectory", lambda prefix: TempDirStub())
    monkeypatch.setattr(ocr_module.shutil, "which", lambda b: "/usr/bin/pdftoppm" if b == "pdftoppm" else None)
    monkeypatch.setattr(ocr_module.subprocess, "run", Mock(return_value=Mock(returncode=0, stdout="", stderr="")))

    images = ocr_module._convert_pdf_to_images(pdf, pdf_max_pages=3, pdf_dpi=200)
    assert len(images) == 3
    for image in images:
        image.unlink(missing_ok=True)


def test_pdf_ocr_uses_existing_tesseract_image_path(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(b"%PDF")

    page1 = tmp_path / "page1.png"
    page2 = tmp_path / "page2.png"
    page1.write_bytes(b"1")
    page2.write_bytes(b"2")

    monkeypatch.setattr(ocr_module.shutil, "which", lambda _: "/usr/bin/tesseract")
    monkeypatch.setattr(ocr_module, "list_tesseract_languages", lambda: ["eng"])
    monkeypatch.setattr(ocr_module, "_convert_pdf_to_images", lambda *_args, **_kwargs: [page1, page2])

    original_run_tesseract = ocr_module.run_tesseract_ocr
    calls: list[str] = []

    def wrapped(path: str, lang: str = "eng", pdf_max_pages: int = 3, pdf_dpi: int = 200):
        calls.append(path)
        if path.endswith(".png"):
            return {
                "status": "completed",
                "result_text": f"text from {Path(path).name}",
                "source_file": path,
                "engine": "tesseract",
                "created_at": "now",
            }
        return original_run_tesseract(path, lang=lang, pdf_max_pages=pdf_max_pages, pdf_dpi=pdf_dpi)

    monkeypatch.setattr(ocr_module, "run_tesseract_ocr", wrapped)

    result = run_ocr(str(pdf), "tesseract")

    assert result["engine"] == "tesseract"
    assert "=== Page 1 ===" in result["result_text"]
    assert "=== Page 2 ===" in result["result_text"]
    assert calls[0].endswith("doc.pdf")
    assert calls[1].endswith("page1.png")
    assert calls[2].endswith("page2.png")
