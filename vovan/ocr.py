from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

DEFAULT_OCR_ENGINE = "placeholder"
SUPPORTED_OCR_ENGINES = {"placeholder", "tesseract"}
SUPPORTED_TESSERACT_INPUT_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".pdf",
}


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
        file_path = Path(path)
        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_TESSERACT_INPUT_EXTENSIONS:
            return {
                "status": "fallback",
                "engine_warning": (
                    f"Tesseract adapter currently supports: {', '.join(sorted(SUPPORTED_TESSERACT_INPUT_EXTENSIONS))}. "
                    f"Got '{extension or '<none>'}', fallback to placeholder."
                ),
            }

        try:
            proc = subprocess.run(
                ["tesseract", str(file_path), "stdout"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            return {
                "status": "fallback",
                "engine_warning": f"Unable to execute tesseract: {exc}. Fallback to placeholder.",
            }

        text = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        if proc.returncode != 0:
            warning = f"Tesseract exited with code {proc.returncode}. Fallback to placeholder."
            if stderr:
                warning = f"{warning} stderr={stderr}"
            return {"status": "fallback", "engine_warning": warning}

        if not text:
            warning = "Tesseract returned empty text. Fallback to placeholder."
            if stderr:
                warning = f"{warning} stderr={stderr}"
            return {"status": "fallback", "engine_warning": warning}

        result = {
            "status": "completed",
            "result_text": text,
            "source_file": str(file_path),
            "engine": self.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if stderr:
            result["engine_warning"] = f"Tesseract stderr: {stderr}"
        return result


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
        if shutil.which("tesseract") is None:
            return PlaceholderOCREngine(), (
                "Engine 'tesseract' requested but binary not found in PATH; fallback to 'placeholder'."
            )
        return TesseractOCREngine(), None

    return PlaceholderOCREngine(), (
        f"Unsupported OCR engine '{requested}'. Supported values: placeholder, tesseract. "
        "Fallback to 'placeholder'."
    )


def run_ocr(path: str, engine_name: str | None = None) -> dict:
    engine, warning = resolve_ocr_engine(engine_name)
    result = engine.run(path)

    if result.get("status") == "fallback":
        fallback_warning = result.get("engine_warning")
        result = run_placeholder_ocr(path)
        if fallback_warning:
            warning = f"{warning} {fallback_warning}".strip() if warning else fallback_warning

    result["engine_requested"] = (engine_name or DEFAULT_OCR_ENGINE).strip().lower()
    result["engine"] = engine.name if result.get("engine") == "tesseract" else DEFAULT_OCR_ENGINE
    if warning:
        result["engine_warning"] = warning
    return result
