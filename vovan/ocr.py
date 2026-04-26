from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

DEFAULT_OCR_ENGINE = "placeholder"
SUPPORTED_OCR_ENGINES = {"placeholder", "tesseract"}
TESSERACT_SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


class OCREngineAdapter(Protocol):
    name: str

    def run(self, path: str) -> dict:
        ...


class PlaceholderOCREngine:
    name = "placeholder"

    def run(self, path: str) -> dict:
        return run_placeholder_ocr(path)


class TesseractOCREngine:
    name = "tesseract"

    def run(self, path: str) -> dict:
        return run_tesseract_ocr(path)


def run_placeholder_ocr(path: str) -> dict:
    file_path = Path(path)
    return {
        "status": "completed",
        "result_text": "placeholder OCR result",
        "source_file": str(file_path),
        "engine": DEFAULT_OCR_ENGINE,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _is_tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _is_tesseract_supported_input(path: Path) -> bool:
    return path.suffix.lower() in TESSERACT_SUPPORTED_SUFFIXES


def run_tesseract_ocr(path: str) -> dict:
    file_path = Path(path)
    if not _is_tesseract_supported_input(file_path):
        raise ValueError(
            f"Tesseract adapter currently supports image files only: {sorted(TESSERACT_SUPPORTED_SUFFIXES)}"
        )

    completed = subprocess.run(
        ["tesseract", str(file_path), "stdout"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or "tesseract failed"
        raise RuntimeError(message)

    return {
        "status": "completed",
        "result_text": completed.stdout.strip(),
        "source_file": str(file_path),
        "engine": "tesseract",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def resolve_ocr_engine(engine_name: str | None) -> tuple[OCREngineAdapter, str | None]:
    requested = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    if requested == "placeholder":
        return PlaceholderOCREngine(), None

    if requested == "tesseract":
        if not _is_tesseract_available():
            return PlaceholderOCREngine(), "Engine 'tesseract' is not installed; fallback to 'placeholder'."
        return TesseractOCREngine(), None

    return PlaceholderOCREngine(), (
        f"Unsupported OCR engine '{requested}'. Supported values: placeholder, tesseract. "
        "Fallback to 'placeholder'."
    )


def run_ocr(path: str, engine_name: str | None = None) -> dict:
    requested = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    engine, warning = resolve_ocr_engine(engine_name)
    try:
        result = engine.run(path)
    except Exception as exc:
        fallback = run_placeholder_ocr(path)
        fallback["engine_requested"] = requested
        fallback["engine"] = DEFAULT_OCR_ENGINE
        fallback["engine_warning"] = (
            f"Engine '{engine.name}' failed or unsupported for this file ({exc}); fallback to 'placeholder'."
        )
        return fallback

    result["engine_requested"] = requested
    result["engine"] = engine.name
    if warning:
        result["engine_warning"] = warning
    return result
