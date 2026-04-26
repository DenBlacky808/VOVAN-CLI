from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def run_placeholder_ocr(path: str) -> dict:
    file_path = Path(path)
    return {
        "status": "completed",
        "result_text": "placeholder OCR result",
        "source_file": str(file_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def run_ocr(path: str, engine: str = "placeholder") -> dict:
    requested_engine = (engine or "placeholder").strip().lower()
    selected_engine = requested_engine
    fallback_reason = None

    if selected_engine not in {"placeholder", "tesseract"}:
        selected_engine = "placeholder"
        fallback_reason = f"Unsupported OCR engine: {requested_engine!r}. Falling back to placeholder."

    if selected_engine == "tesseract":
        selected_engine = "placeholder"
        fallback_reason = "OCR engine 'tesseract' is planned but not implemented yet. Falling back to placeholder."

    result = run_placeholder_ocr(path)
    result["engine_requested"] = requested_engine
    result["engine_used"] = selected_engine
    if fallback_reason:
        result["engine_fallback_reason"] = fallback_reason
    return result
