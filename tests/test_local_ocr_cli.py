from pathlib import Path
from types import SimpleNamespace

from vovan import local_ocr


def test_extract_image_text_returns_real_tesseract_text(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / "scan.png"
    image.write_bytes(b"fake")

    monkeypatch.setattr(local_ocr, "_is_tesseract_available", lambda: True)
    monkeypatch.setattr(
        local_ocr,
        "run_tesseract_ocr",
        lambda path, lang: {"result_text": " recognized text \n"},
    )

    assert local_ocr.extract_image_text(str(image), lang="eng") == "recognized text"


def test_extract_file_text_rejects_unsupported_type(tmp_path: Path) -> None:
    file_path = tmp_path / "scan.txt"
    file_path.write_bytes(b"fake")

    try:
        local_ocr.extract_file_text(str(file_path))
    except ValueError as exc:
        assert "supported formats" in str(exc)
    else:
        raise AssertionError("expected unsupported file error")


def test_extract_image_text_errors_when_tesseract_missing(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / "scan.jpg"
    image.write_bytes(b"fake")

    monkeypatch.setattr(local_ocr, "_is_tesseract_available", lambda: False)

    try:
        local_ocr.extract_image_text(str(image))
    except RuntimeError as exc:
        assert "brew install tesseract" in str(exc)
    else:
        raise AssertionError("expected missing tesseract error")


def test_main_returns_nonzero_for_empty_ocr(monkeypatch, tmp_path: Path, capsys) -> None:
    image = tmp_path / "scan.jpeg"
    image.write_bytes(b"fake")

    monkeypatch.setattr(local_ocr, "_is_tesseract_available", lambda: True)
    monkeypatch.setattr(local_ocr, "run_tesseract_ocr", lambda path, lang: {"result_text": ""})

    code = local_ocr.main([str(image)])

    assert code == 1
    assert "OCR output is empty" in capsys.readouterr().err


def test_extract_file_text_joins_pdf_pages_with_markers(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr(local_ocr, "_is_tesseract_available", lambda: True)
    monkeypatch.setattr(local_ocr, "_is_pdftoppm_available", lambda: True)

    raster_calls: list[list[str]] = []

    def fake_run(cmd, capture_output, text, check):
        raster_calls.append(cmd)
        output_prefix = Path(cmd[-1])
        (output_prefix.parent / "page-1.png").write_bytes(b"page 1")
        (output_prefix.parent / "page-2.png").write_bytes(b"page 2")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(local_ocr.subprocess, "run", fake_run)

    ocr_calls: list[tuple[str, str]] = []

    def fake_ocr(path: str, lang: str) -> dict:
        ocr_calls.append((path, lang))
        return {"result_text": f" text from {Path(path).stem} \n"}

    monkeypatch.setattr(local_ocr, "run_tesseract_ocr", fake_ocr)

    text = local_ocr.extract_file_text(str(pdf), lang="rus+eng", pdf_dpi=250)

    assert text == "--- page 1 ---\ntext from page-1\n\n--- page 2 ---\ntext from page-2"
    assert raster_calls[0][0:4] == ["pdftoppm", "-r", "250", "-png"]
    assert raster_calls[0][-2] == str(pdf)
    assert [Path(path).name for path, _ in ocr_calls] == ["page-1.png", "page-2.png"]
    assert [lang for _, lang in ocr_calls] == ["rus+eng", "rus+eng"]


def test_extract_pdf_text_errors_when_pdftoppm_missing(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr(local_ocr, "_is_tesseract_available", lambda: True)
    monkeypatch.setattr(local_ocr, "_is_pdftoppm_available", lambda: False)

    try:
        local_ocr.extract_pdf_text(str(pdf))
    except RuntimeError as exc:
        assert "brew install poppler" in str(exc)
    else:
        raise AssertionError("expected missing pdftoppm error")


def test_extract_pdf_text_keeps_marker_for_empty_page(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "empty-page.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr(local_ocr, "_is_tesseract_available", lambda: True)
    monkeypatch.setattr(local_ocr, "_is_pdftoppm_available", lambda: True)

    def fake_run(cmd, capture_output, text, check):
        output_prefix = Path(cmd[-1])
        (output_prefix.parent / "page-1.png").write_bytes(b"page 1")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(local_ocr.subprocess, "run", fake_run)
    monkeypatch.setattr(local_ocr, "run_tesseract_ocr", lambda path, lang: {"result_text": " \n"})

    assert local_ocr.extract_pdf_text(str(pdf)) == "--- page 1 ---\n[empty OCR output]"


def test_main_accepts_pdf_path(monkeypatch, tmp_path: Path, capsys) -> None:
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
    captured = {}

    def fake_extract(path: str, lang: str, pdf_dpi: int) -> str:
        captured["path"] = path
        captured["lang"] = lang
        captured["pdf_dpi"] = pdf_dpi
        return "--- page 1 ---\nmain pdf text"

    monkeypatch.setattr(local_ocr, "extract_file_text", fake_extract)

    code = local_ocr.main(["--lang", "rus+eng", "--pdf-dpi", "250", str(pdf)])

    assert code == 0
    assert captured == {"path": str(pdf), "lang": "rus+eng", "pdf_dpi": 250}
    assert "--- page 1 ---\nmain pdf text" in capsys.readouterr().out
