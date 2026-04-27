from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from vovan.ocr import _is_pdftoppm_available, _is_tesseract_available, run_tesseract_ocr

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
SUPPORTED_PDF_SUFFIXES = {".pdf"}
SUPPORTED_FILE_SUFFIXES = SUPPORTED_IMAGE_SUFFIXES | SUPPORTED_PDF_SUFFIXES
DEFAULT_PDF_DPI = 200
EMPTY_PDF_PAGE_TEXT = "[empty OCR output]"


def _supported_formats() -> str:
    return ", ".join(sorted(SUPPORTED_FILE_SUFFIXES))


def _ensure_existing_file(file_path: Path) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"path is not a file: {file_path}")


def _ensure_tesseract_available() -> None:
    if not _is_tesseract_available():
        raise RuntimeError("tesseract is not installed or not on PATH; install it with: brew install tesseract")


def _page_image_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"-(\d+)\.png$", path.name)
    if match:
        return int(match.group(1)), path.name
    return sys.maxsize, path.name


def render_pdf_pages(pdf_path: Path, output_dir: Path, dpi: int = DEFAULT_PDF_DPI) -> list[Path]:
    output_prefix = output_dir / "page"
    completed = subprocess.run(
        [
            "pdftoppm",
            "-r",
            str(max(72, dpi)),
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

    page_paths = sorted(output_dir.glob("page-*.png"), key=_page_image_sort_key)
    if not page_paths:
        raise RuntimeError("pdftoppm produced no page images from PDF")
    return page_paths


def extract_image_text(path: str, lang: str = "eng") -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_SUFFIXES))
        raise ValueError(f"unsupported file type '{suffix or '(none)'}'; supported formats: {supported}")
    _ensure_existing_file(file_path)
    _ensure_tesseract_available()

    result = run_tesseract_ocr(str(file_path), lang=lang)
    text = result.get("result_text", "").strip()
    if not text:
        raise RuntimeError("OCR output is empty; check image quality, language pack, or try a clearer PNG/JPG")
    return text


def extract_pdf_text(path: str, lang: str = "eng", pdf_dpi: int = DEFAULT_PDF_DPI) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix not in SUPPORTED_PDF_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_PDF_SUFFIXES))
        raise ValueError(f"unsupported file type '{suffix or '(none)'}'; supported formats: {supported}")
    _ensure_existing_file(file_path)
    _ensure_tesseract_available()
    if not _is_pdftoppm_available():
        raise RuntimeError(
            "pdftoppm is not installed or not on PATH; install Poppler with: brew install poppler"
        )

    with tempfile.TemporaryDirectory(prefix="vovan_local_pdf_ocr_") as temp_dir:
        page_paths = render_pdf_pages(file_path, Path(temp_dir), dpi=pdf_dpi)
        page_texts: list[str] = []
        for idx, page_path in enumerate(page_paths, start=1):
            result = run_tesseract_ocr(str(page_path), lang=lang)
            page_text = result.get("result_text", "").strip() or EMPTY_PDF_PAGE_TEXT
            page_texts.append(f"--- page {idx} ---\n{page_text}")

    return "\n\n".join(page_texts)


def extract_file_text(path: str, lang: str = "eng", pdf_dpi: int = DEFAULT_PDF_DPI) -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return extract_image_text(path, lang=lang)
    if suffix in SUPPORTED_PDF_SUFFIXES:
        return extract_pdf_text(path, lang=lang, pdf_dpi=pdf_dpi)
    raise ValueError(f"unsupported file type '{suffix or '(none)'}'; supported formats: {_supported_formats()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m vovan.local_ocr",
        description="Extract text from a local PNG/JPG/JPEG/PDF file using Tesseract.",
    )
    parser.add_argument("path", help="Path to a .png, .jpg, .jpeg, or .pdf file")
    parser.add_argument(
        "--lang",
        default=os.getenv("VOVAN_TESSERACT_LANG", "eng"),
        help="Tesseract language code, for example eng or rus+eng",
    )
    parser.add_argument(
        "--pdf-dpi",
        type=int,
        default=DEFAULT_PDF_DPI,
        help="PDF rasterization DPI for pdftoppm; values below 72 are raised to 72",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = extract_file_text(args.path, lang=args.lang, pdf_dpi=args.pdf_dpi)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
