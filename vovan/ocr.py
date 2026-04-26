from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def run_placeholder_ocr(path: str) -> dict:
    file_path = Path(path)
    return {
        "status": "completed",
        "result_text": "OCR MVP placeholder for PDF.",
        "source_file": str(file_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
