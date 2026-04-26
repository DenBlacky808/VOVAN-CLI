from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

DEFAULT_OCR_ENGINE = "placeholder"
SUPPORTED_OCR_ENGINES = {"placeholder", "tesseract"}


class OCREngineAdapter(Protocol):
    name: str

    def run(self, path: str) -> dict:
        ...


class PlaceholderOCREngine:
    name = "placeholder"

    def run(self, path: str) -> dict:
        return run_placeholder_ocr(path)


def run_placeholder_ocr(path: str) -> dict:
    file_path = Path(path)
    return {
        "status": "completed",
        "result_text": "placeholder OCR result",
        "source_file": str(file_path),
        "engine": DEFAULT_OCR_ENGINE,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def resolve_ocr_engine(engine_name: str | None) -> tuple[OCREngineAdapter, str | None]:
    requested = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    if requested == "placeholder":
        return PlaceholderOCREngine(), None

    if requested == "tesseract":
        return PlaceholderOCREngine(), "Engine 'tesseract' is planned but not available yet; fallback to 'placeholder'."

    return PlaceholderOCREngine(), (
        f"Unsupported OCR engine '{requested}'. Supported values: placeholder, tesseract. "
        "Fallback to 'placeholder'."
    )


def run_ocr(path: str, engine_name: str | None = None) -> dict:
    engine, warning = resolve_ocr_engine(engine_name)
    result = engine.run(path)
    result["engine_requested"] = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    result["engine"] = engine.name
    if warning:
        result["engine_warning"] = warning
    return result
