from vovan.ocr import run_ocr, run_placeholder_ocr


def test_ocr_placeholder_contract() -> None:
    result = run_placeholder_ocr("/tmp/demo.pdf")
    assert result["status"] == "completed"
    assert result["result_text"] == "placeholder OCR result"
    assert result["source_file"] == "/tmp/demo.pdf"
    assert result["engine_used"] == "placeholder"
    assert "created_at" in result


def test_ocr_unsupported_engine_falls_back_safely() -> None:
    result = run_ocr("/tmp/demo.pdf", engine="unknown-engine")
    assert result["status"] == "completed"
    assert result["result_text"] == "placeholder OCR result"
    assert result["engine_requested"] == "unknown-engine"
    assert result["engine_used"] == "placeholder"
    assert result["engine_fallback"] is True
    assert "Unsupported OCR engine" in result["engine_message"]
