from vovan.ocr import run_ocr, run_placeholder_ocr


def test_ocr_placeholder_contract() -> None:
    result = run_placeholder_ocr("/tmp/demo.pdf")
    assert result["status"] == "completed"
    assert result["result_text"] == "placeholder OCR result"
    assert result["source_file"] == "/tmp/demo.pdf"
    assert "created_at" in result


def test_ocr_adapter_uses_placeholder_by_default() -> None:
    result = run_ocr("/tmp/demo.pdf")
    assert result["result_text"] == "placeholder OCR result"
    assert result["engine_requested"] == "placeholder"
    assert result["engine_used"] == "placeholder"


def test_ocr_adapter_handles_unsupported_engine() -> None:
    result = run_ocr("/tmp/demo.pdf", engine="unknown")
    assert result["engine_requested"] == "unknown"
    assert result["engine_used"] == "placeholder"
    assert "unsupported" in result["engine_fallback_reason"].lower()
