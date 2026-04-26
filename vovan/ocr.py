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
    if requested_engine == "placeholder":
        result = run_placeholder_ocr(path)
        result["engine"] = "placeholder"
        return result

    if requested_engine == "tesseract":
        result = run_placeholder_ocr(path)
        result["engine"] = "placeholder"
        result["requested_engine"] = "tesseract"
        result["warning"] = "tesseract engine is not enabled in this build; used placeholder fallback"
        return result

    result = run_placeholder_ocr(path)
    result["engine"] = "placeholder"
    result["requested_engine"] = requested_engine
    result["warning"] = f"unsupported OCR engine '{requested_engine}'; used placeholder fallback"
    return result
