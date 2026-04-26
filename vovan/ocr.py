from __future__ import annotations

import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from vovan.analysis import build_document_analysis

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
        return run_tesseract_ocr_with_pdf_preprocessing(
            path,
            lang=self.lang,
            pdf_max_pages=self.pdf_max_pages,
            pdf_dpi=self.pdf_dpi,
        )


class PdftoppmPreprocessor:
    name = "pdftoppm"

    def __init__(self, dpi: int = 200, max_pages: int = 3) -> None:
        self.dpi = max(72, dpi)
        self.max_pages = max(1, max_pages)

    def convert_pdf_to_images(self, pdf_path: Path, output_dir: Path) -> list[Path]:
        output_prefix = output_dir / "page"
        completed = subprocess.run(
            [
                "pdftoppm",
                "-f",
                "1",
                "-l",
                str(self.max_pages),
                "-r",
                str(self.dpi),
                "-png",
                str(pdf_path),
                str(output_prefix),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or "pdftoppm failed"
            raise RuntimeError(message)

        generated = sorted(output_dir.glob("page-*.png"))
        if not generated:
            raise RuntimeError("pdftoppm produced no PNG pages")
        return generated


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


def _is_tesseract_supported_input(path: Path) -> bool:
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


def run_tesseract_ocr_with_pdf_preprocessing(path: str, lang: str = "eng", pdf_max_pages: int = 3, pdf_dpi: int = 200) -> dict:
    file_path = Path(path)
    if _is_tesseract_supported_input(file_path):
        return run_tesseract_ocr(path, lang=lang)

    if not _is_pdf_input(file_path):
        raise ValueError(
            f"Tesseract adapter currently supports image files or PDF preprocessing: "
            f"{sorted(TESSERACT_SUPPORTED_SUFFIXES | PDF_SUPPORTED_SUFFIXES)}"
        )

    if not _is_pdftoppm_available():
        raise RuntimeError("pdftoppm is not installed; cannot preprocess PDF for tesseract OCR")

    preprocessor = PdftoppmPreprocessor(dpi=pdf_dpi, max_pages=pdf_max_pages)

    with tempfile.TemporaryDirectory(prefix="vovan_pdf_ocr_") as temp_dir:
        page_paths = preprocessor.convert_pdf_to_images(file_path, Path(temp_dir))
        page_texts: list[str] = []
        for idx, page_path in enumerate(page_paths, start=1):
            page_result = run_tesseract_ocr(str(page_path), lang=lang)
            page_text = page_result.get("result_text", "")
            page_texts.append(f"\n--- PAGE {idx} ---\n{page_text}".strip())

    return {
        "status": "completed",
        "result_text": "\n\n".join(page_texts).strip(),
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
        fallback.update(build_document_analysis(fallback.get("result_text", "")))
        return fallback

    result["engine_requested"] = requested
    result["engine"] = engine.name

    analysis = build_document_analysis(result.get("result_text", ""))
    result.update(analysis)

    if warning:
        result["engine_warning"] = warning
    return result
