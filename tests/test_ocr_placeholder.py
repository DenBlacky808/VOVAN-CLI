from vovan.ocr import run_ocr, run_placeholder_ocr


def test_ocr_placeholder_contract() -> None:
    result = run_placeholder_ocr("/tmp/demo.pdf")
    assert result["status"] == "completed"
    assert result["result_text"] == "placeholder OCR result"
    assert result["source_file"] == "/tmp/demo.pdf"
    assert "created_at" in result


def test_ocr_engine_placeholder_default() -> None:
    result = run_ocr("/tmp/demo.pdf")
    assert result["engine"] == "placeholder"
    assert result["result_text"] == "placeholder OCR result"


def test_ocr_engine_unsupported_fallback() -> None:
    result = run_ocr("/tmp/demo.pdf", engine="unknown")
    assert result["engine"] == "placeholder"
    assert "warning" in result
