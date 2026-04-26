from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def run_ocr_placeholder(path: str) -> dict:
    file_path = Path(path)
    return {
        "status": "completed",
        "result_text": "placeholder OCR result",
        "source_file": str(file_path),
        "created_at": datetime.now(UTC).isoformat(),
    }
