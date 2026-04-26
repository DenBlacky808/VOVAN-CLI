from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

SUPPORTED_OCR_ENGINES = {"placeholder", "tesseract"}


def run_placeholder_ocr(path: str) -> dict:
    file_path = Path(path)
    return {
        "status": "completed",
        "result_text": "placeholder OCR result",
        "source_file": str(file_path),
        "engine_used": "placeholder",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def run_ocr(path: str, engine: str = "placeholder") -> dict:
    requested_engine = (engine or "placeholder").strip().lower()
    engine_used = requested_engine
    engine_message = None
    fallback_used = False

    if requested_engine not in SUPPORTED_OCR_ENGINES:
        engine_used = "placeholder"
        fallback_used = True
        engine_message = f"Unsupported OCR engine '{requested_engine}', falling back to placeholder."
    elif requested_engine == "tesseract":
        engine_used = "placeholder"
        fallback_used = True
        engine_message = "OCR engine 'tesseract' is planned but not installed yet; using placeholder."

    result = run_placeholder_ocr(path)
    result["engine_requested"] = requested_engine
    result["engine_used"] = engine_used
    result["engine_fallback"] = fallback_used
    if engine_message:
        result["engine_message"] = engine_message
    return result
