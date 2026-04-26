from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from vovan.config import Settings


def write_report(settings: Settings, mode: str, payload: dict) -> Path:
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_file = settings.report_dir / f"report_{mode}_{ts}.md"

    ocr_engine = payload.get("ocr_engine")
    if ocr_engine is None and isinstance(payload.get("ocr"), dict):
        ocr_engine = payload["ocr"].get("engine")

    lines = [
        "# VOVAN Report",
        "",
        f"- created_at_utc: {datetime.now(timezone.utc).isoformat()}",
        f"- mode: {mode}",
        f"- ocr_engine: {ocr_engine if ocr_engine else 'n/a'}",
        "",
        "## Payload",
        "```",
        str(payload),
        "```",
    ]

    report_file.write_text("\n".join(lines), encoding="utf-8")
    return report_file
