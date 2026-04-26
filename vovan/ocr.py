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

    def __init__(self, lang: str = "eng") -> None:
        self.lang = lang

    def run(self, path: str) -> dict:
        return run_tesseract_ocr(path, self.lang)


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


def list_tesseract_languages() -> list[str]:
    if not _is_tesseract_available():
        return []

    completed = subprocess.run(
        ["tesseract", "--list-langs"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []

    languages = []
    for line in completed.stdout.splitlines():
        value = line.strip()
        if not value or value.lower().startswith("list of available languages"):
            continue
        languages.append(value)
    return languages


def run_tesseract_ocr(path: str, lang: str = "eng") -> dict:
    file_path = Path(path)
    if not _is_tesseract_supported_input(file_path):
        raise ValueError(
            f"Tesseract adapter currently supports image files only: {sorted(TESSERACT_SUPPORTED_SUFFIXES)}"
        )

    requested_languages = [token.strip() for token in lang.split("+") if token.strip()]
    available_languages = list_tesseract_languages()
    missing_languages = [token for token in requested_languages if token not in available_languages]
    if requested_languages and available_languages and missing_languages:
        raise RuntimeError(
            f"Requested tesseract language(s) not installed: {', '.join(missing_languages)}."
        )

    completed = subprocess.run(
        ["tesseract", str(file_path), "stdout", "-l", lang],
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


def resolve_ocr_engine(engine_name: str | None, tesseract_lang: str = "eng") -> tuple[OCREngineAdapter, str | None]:
    requested = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    if requested == "placeholder":
        return PlaceholderOCREngine(), None

    if requested == "tesseract":
        if not _is_tesseract_available():
            return PlaceholderOCREngine(), "Engine 'tesseract' is not installed; fallback to 'placeholder'."
        return TesseractOCREngine(lang=tesseract_lang), None

    return PlaceholderOCREngine(), (
        f"Unsupported OCR engine '{requested}'. Supported values: placeholder, tesseract. "
        "Fallback to 'placeholder'."
    )


def run_ocr(path: str, engine_name: str | None = None, tesseract_lang: str = "eng") -> dict:
    requested = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    engine, warning = resolve_ocr_engine(engine_name, tesseract_lang=tesseract_lang)
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
