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
PDF_SUFFIXES = {".pdf"}


class OCREngineAdapter(Protocol):
    name: str

    def run(self, path: str) -> dict:
        ...


class PDFPreprocessorAdapter(Protocol):
    name: str

    def run(self, path: Path, output_dir: Path, dpi: int, max_pages: int) -> list[Path]:
        ...


class PlaceholderOCREngine:
    name = "placeholder"

    def run(self, path: str) -> dict:
        return run_placeholder_ocr(path)


class TesseractOCREngine:
    name = "tesseract"

    def __init__(self, lang: str = "eng", pdf_max_pages: int = 3, pdf_dpi: int = 200) -> None:
        self.lang = lang
        self.pdf_max_pages = pdf_max_pages
        self.pdf_dpi = pdf_dpi

    def run(self, path: str) -> dict:
        return run_tesseract_ocr(path, self.lang, pdf_max_pages=self.pdf_max_pages, pdf_dpi=self.pdf_dpi)


class PdftoppmPDFPreprocessor:
    name = "pdftoppm"

    def run(self, path: Path, output_dir: Path, dpi: int, max_pages: int) -> list[Path]:
        return convert_pdf_to_png_images(path, output_dir=output_dir, dpi=dpi, max_pages=max_pages)


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
    return path.suffix.lower() in TESSERACT_SUPPORTED_SUFFIXES | PDF_SUFFIXES


def _is_pdftoppm_available() -> bool:
    return shutil.which("pdftoppm") is not None


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


def convert_pdf_to_png_images(path: Path, output_dir: Path, dpi: int = 200, max_pages: int = 3) -> list[Path]:
    if not _is_pdftoppm_available():
        raise RuntimeError("pdftoppm is not installed; cannot preprocess PDF for tesseract OCR.")

    output_prefix = output_dir / "page"
    completed = subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r",
            str(dpi),
            "-f",
            "1",
            "-l",
            str(max_pages),
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

    return sorted(output_dir.glob("page-*.png"))


def run_tesseract_ocr(path: str, lang: str = "eng", pdf_max_pages: int = 3, pdf_dpi: int = 200) -> dict:
    file_path = Path(path)
    if not _is_tesseract_supported_input(file_path):
        raise ValueError(
            f"Tesseract adapter currently supports files: {sorted(TESSERACT_SUPPORTED_SUFFIXES | PDF_SUFFIXES)}"
        )

    requested_languages = [token.strip() for token in lang.split("+") if token.strip()]
    available_languages = list_tesseract_languages()
    missing_languages = [token for token in requested_languages if token not in available_languages]
    if requested_languages and available_languages and missing_languages:
        raise RuntimeError(
            f"Requested tesseract language(s) not installed: {', '.join(missing_languages)}."
        )

    if file_path.suffix.lower() in PDF_SUFFIXES:
        preprocessor: PDFPreprocessorAdapter = PdftoppmPDFPreprocessor()
        with tempfile.TemporaryDirectory(prefix="vovan_pdf_ocr_") as temp_dir:
            pages = preprocessor.run(file_path, Path(temp_dir), dpi=pdf_dpi, max_pages=pdf_max_pages)
            if not pages:
                raise RuntimeError("pdftoppm did not generate any PNG pages from PDF.")

            page_texts: list[str] = []
            for idx, page in enumerate(pages, start=1):
                completed = subprocess.run(
                    ["tesseract", str(page), "stdout", "-l", lang],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if completed.returncode != 0:
                    message = completed.stderr.strip() or f"tesseract failed on page {idx}"
                    raise RuntimeError(message)
                page_texts.append(f"--- page {idx} ---\n{completed.stdout.strip()}")

            result_text = "\n\n".join(page_texts)
    else:
        completed = subprocess.run(
            ["tesseract", str(file_path), "stdout", "-l", lang],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or "tesseract failed"
            raise RuntimeError(message)
        result_text = completed.stdout.strip()

    return {
        "status": "completed",
        "result_text": result_text,
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
