from vovan.ocr import run_ocr_placeholder


def test_ocr_placeholder_has_expected_fields() -> None:
    payload = run_ocr_placeholder("data/input.png")
    assert payload["status"] == "completed"
    assert payload["result_text"] == "placeholder OCR result"
    assert payload["source_file"] == "data/input.png"
    assert "created_at" in payload
