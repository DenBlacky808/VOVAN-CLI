from __future__ import annotations

import mimetypes
from pathlib import Path

from vovan.config import Settings


def run_preflight(path: str, settings: Settings) -> dict:
    file_path = Path(path)
    exists = file_path.exists()
    is_file = file_path.is_file()

    extension = file_path.suffix.lower()
    size_bytes = file_path.stat().st_size if exists and is_file else 0
    mime_type = mimetypes.guess_type(str(file_path))[0]

    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    extension_ok = extension in settings.allowed_extensions if extension else False
    size_ok = size_bytes <= max_size_bytes

    suitable_for_ocr = exists and is_file and extension_ok and size_ok

    return {
        "source_file": str(file_path),
        "exists": exists,
        "is_file": is_file,
        "size_bytes": size_bytes,
        "extension": extension,
        "mime_type": mime_type,
        "allowed_extensions": sorted(settings.allowed_extensions),
        "max_size_bytes": max_size_bytes,
        "extension_ok": extension_ok,
        "size_ok": size_ok,
        "suitable_for_ocr": suitable_for_ocr,
    }
