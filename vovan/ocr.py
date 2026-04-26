from __future__ import annotations

import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

DEFAULT_OCR_ENGINE = "placeholder"
SUPPORTED_OCR_ENGINES = {"placeholder", "tesseract"}
TESSERACT_SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
PDF_SUPPORTED_SUFFIXES = {".pdf"}


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

    def __init__(self, lang: str = "eng", pdf_max_pages: int = 3, pdf_dpi: int = 200) -> None:
        self.lang = lang
        self.pdf_max_pages = max(1, pdf_max_pages)
        self.pdf_dpi = max(72, pdf_dpi)

    def run(self, path: str) -> dict:
        return run_tesseract_ocr(path, self.lang, pdf_max_pages=self.pdf_max_pages, pdf_dpi=self.pdf_dpi)


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


def _is_pdftoppm_available() -> bool:
    return shutil.which("pdftoppm") is not None


def _is_tesseract_supported_image(path: Path) -> bool:
    return path.suffix.lower() in TESSERACT_SUPPORTED_SUFFIXES


def _is_pdf_input(path: Path) -> bool:
    return path.suffix.lower() in PDF_SUPPORTED_SUFFIXES


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


def _convert_pdf_to_images(path: Path, pdf_max_pages: int, pdf_dpi: int) -> list[Path]:
    if not _is_pdftoppm_available():
        raise RuntimeError("PDF preprocessing tool 'pdftoppm' is not installed")

    with tempfile.TemporaryDirectory(prefix="vovan-pdf-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        output_prefix = tmp_path / "page"
        completed = subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r",
                str(max(72, pdf_dpi)),
                "-f",
                "1",
                "-l",
                str(max(1, pdf_max_pages)),
                str(path),
                str(output_prefix),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or "pdftoppm failed"
            raise RuntimeError(message)

        image_paths = sorted(tmp_path.glob("page-*.png"))
        if not image_paths:
            raise RuntimeError("pdftoppm produced no page images")

        persisted_paths: list[Path] = []
        for image_path in image_paths[: max(1, pdf_max_pages)]:
            named = tempfile.NamedTemporaryFile(prefix="vovan-page-", suffix=".png", delete=False)
            named.close()
            persist_path = Path(named.name)
            persist_path.write_bytes(image_path.read_bytes())
            persisted_paths.append(persist_path)

    return persisted_paths


def run_tesseract_ocr(path: str, lang: str = "eng", pdf_max_pages: int = 3, pdf_dpi: int = 200) -> dict:
    file_path = Path(path)

    requested_languages = [token.strip() for token in lang.split("+") if token.strip()]
    available_languages = list_tesseract_languages()
    missing_languages = [token for token in requested_languages if token not in available_languages]
    if requested_languages and available_languages and missing_languages:
        raise RuntimeError(
            f"Requested tesseract language(s) not installed: {', '.join(missing_languages)}."
        )

    if _is_pdf_input(file_path):
        temp_images = _convert_pdf_to_images(file_path, pdf_max_pages=pdf_max_pages, pdf_dpi=pdf_dpi)
        try:
            page_texts = []
            for index, image_path in enumerate(temp_images, start=1):
                page_result = run_tesseract_ocr(str(image_path), lang=lang, pdf_max_pages=pdf_max_pages, pdf_dpi=pdf_dpi)
                page_texts.append(f"=== Page {index} ===\n{page_result['result_text']}")
        finally:
            for image_path in temp_images:
                image_path.unlink(missing_ok=True)

        return {
            "status": "completed",
            "result_text": "\n\n".join(page_texts).strip(),
            "source_file": str(file_path),
            "engine": "tesseract",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    if not _is_tesseract_supported_image(file_path):
        raise ValueError(
            f"Tesseract adapter currently supports image files only: {sorted(TESSERACT_SUPPORTED_SUFFIXES)}"
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


def resolve_ocr_engine(
    engine_name: str | None,
    tesseract_lang: str = "eng",
    pdf_max_pages: int = 3,
    pdf_dpi: int = 200,
) -> tuple[OCREngineAdapter, str | None]:
    requested = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    if requested == "placeholder":
        return PlaceholderOCREngine(), None

    if requested == "tesseract":
        if not _is_tesseract_available():
            return PlaceholderOCREngine(), "Engine 'tesseract' is not installed; fallback to 'placeholder'."
        return TesseractOCREngine(lang=tesseract_lang, pdf_max_pages=pdf_max_pages, pdf_dpi=pdf_dpi), None

    return PlaceholderOCREngine(), (
        f"Unsupported OCR engine '{requested}'. Supported values: placeholder, tesseract. "
        "Fallback to 'placeholder'."
    )


def run_ocr(
    path: str,
    engine_name: str | None = None,
    tesseract_lang: str = "eng",
    pdf_max_pages: int = 3,
    pdf_dpi: int = 200,
) -> dict:
    requested = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    engine, warning = resolve_ocr_engine(
        engine_name,
        tesseract_lang=tesseract_lang,
        pdf_max_pages=pdf_max_pages,
        pdf_dpi=pdf_dpi,
    )
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
