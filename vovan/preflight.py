from __future__ import annotations

import mimetypes
from pathlib import Path

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".tif", ".tiff", ".bmp"}


def run_preflight(path: str) -> dict:
    file_path = Path(path)
    exists = file_path.exists()
    size = file_path.stat().st_size if exists and file_path.is_file() else 0
    ext = file_path.suffix.lower()
    mime, _ = mimetypes.guess_type(file_path.name)
    suitable = exists and file_path.is_file() and size > 0 and ext in ALLOWED_EXTENSIONS

    checks = {
        "exists": exists,
        "is_file": file_path.is_file() if exists else False,
        "size_bytes": size,
        "extension": ext,
        "allowed_extension": ext in ALLOWED_EXTENSIONS,
        "mime_type": mime,
        "suitable_for_ocr": suitable,
    }

    return {
        "status": "ok" if suitable else "failed",
        "path": str(file_path),
        "checks": checks,
    }
