from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from vovan.ocr import _is_tesseract_available, run_tesseract_ocr

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def extract_image_text(path: str, lang: str = "eng") -> str:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_SUFFIXES))
        raise ValueError(f"unsupported file type '{suffix or '(none)'}'; supported formats: {supported}")
    if not file_path.exists():
        raise FileNotFoundError(f"file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"path is not a file: {file_path}")
    if not _is_tesseract_available():
        raise RuntimeError("tesseract is not installed or not on PATH; install it with: brew install tesseract")

    result = run_tesseract_ocr(str(file_path), lang=lang)
    text = result.get("result_text", "").strip()
    if not text:
        raise RuntimeError("OCR output is empty; check image quality, language pack, or try a clearer PNG/JPG")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m vovan.local_ocr",
        description="Extract text from a local PNG/JPG/JPEG image using Tesseract.",
    )
    parser.add_argument("path", help="Path to a .png, .jpg, or .jpeg image")
    parser.add_argument(
        "--lang",
        default=os.getenv("VOVAN_TESSERACT_LANG", "eng"),
        help="Tesseract language code, for example eng or rus+eng",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text = extract_image_text(args.path, lang=args.lang)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
