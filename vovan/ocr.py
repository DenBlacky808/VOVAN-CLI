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


def _get_tesseract_path() -> str | None:
    return shutil.which("tesseract")


def list_tesseract_languages() -> list[str]:
    tesseract_path = _get_tesseract_path()
    if not tesseract_path:
        return []

    completed = subprocess.run(
        [tesseract_path, "--list-langs"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return []

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    return [line for line in lines if line and not line.lower().startswith("list of available languages")]


def _is_tesseract_lang_available(requested_lang: str, installed_langs: list[str]) -> bool:
    requested = [part.strip() for part in requested_lang.split("+") if part.strip()]
    if not requested:
        requested = ["eng"]
    installed = set(installed_langs)
    return all(lang in installed for lang in requested)


def _is_tesseract_supported_input(path: Path) -> bool:
    return path.suffix.lower() in TESSERACT_SUPPORTED_SUFFIXES


def run_tesseract_ocr(path: str, lang: str = "eng") -> dict:
    file_path = Path(path)
    if not _is_tesseract_supported_input(file_path):
        raise ValueError(
            f"Tesseract adapter currently supports image files only: {sorted(TESSERACT_SUPPORTED_SUFFIXES)}"
        )

    installed_langs = list_tesseract_languages()
    if installed_langs and not _is_tesseract_lang_available(lang, installed_langs):
        raise ValueError(
            f"Configured tesseract language '{lang}' is not installed; "
            f"installed languages: {', '.join(installed_langs)}"
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


def run_ocr(path: str, engine_name: str | None = None, tesseract_lang: str = "eng") -> dict:
    requested = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    engine, warning = resolve_ocr_engine(engine_name)
    if requested == "tesseract" and isinstance(engine, TesseractOCREngine):
        engine = TesseractOCREngine(tesseract_lang)
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


def inspect_tesseract(configured_lang: str) -> dict:
    tesseract_path = _get_tesseract_path()
    available = tesseract_path is not None
    installed_languages = list_tesseract_languages() if available else []
    configured_available = (
        _is_tesseract_lang_available(configured_lang, installed_languages) if installed_languages else False
    )
    return {
        "tesseract_available": available,
        "tesseract_path": tesseract_path,
        "tesseract_languages_available": installed_languages,
        "tesseract_lang_configured": configured_lang,
        "tesseract_lang_available": configured_available,
    }
