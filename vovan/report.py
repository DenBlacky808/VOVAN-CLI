from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def write_report(mode: str, payload: dict, reports_dir: Path) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = reports_dir / f"report_{mode}_{ts}.md"

    lines = [
        "# VOVAN Report",
        "",
        f"- created_at: {datetime.now(UTC).isoformat()}",
        f"- mode: {mode}",
        "",
        "## Payload",
        "```json",
        str(payload),
        "```",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
