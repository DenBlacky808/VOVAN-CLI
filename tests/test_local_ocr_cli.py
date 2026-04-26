from pathlib import Path

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


def test_extract_image_text_rejects_unsupported_type(tmp_path: Path) -> None:
    file_path = tmp_path / "scan.pdf"
    file_path.write_bytes(b"fake")

    try:
        local_ocr.extract_image_text(str(file_path))
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
