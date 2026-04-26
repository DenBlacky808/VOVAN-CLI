from vovan.ocr import run_placeholder_ocr


def test_ocr_placeholder_contract() -> None:
    result = run_placeholder_ocr("/tmp/demo.pdf")
    assert result["status"] == "completed"
    assert result["result_text"] == "placeholder OCR result"
    assert result["source_file"] == "/tmp/demo.pdf"
    assert "created_at" in result
