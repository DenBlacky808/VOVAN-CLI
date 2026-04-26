from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file(env_file: str) -> None:
    path = Path(env_file)
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(slots=True)
class Settings:
    vladcher_base_url: str
    vovan_worker_token: str
    data_dir: Path = Path("data")
    logs_dir: Path = Path("logs")
    reports_dir: Path = Path("reports")
    dry_run: bool = True


REQUIRED_KEYS = ("VLADCHER_BASE_URL", "VOVAN_WORKER_TOKEN")


def load_settings(env_file: str = ".env") -> Settings:
    _load_env_file(env_file)
    return Settings(
        vladcher_base_url=os.getenv("VLADCHER_BASE_URL", "").strip(),
        vovan_worker_token=os.getenv("VOVAN_WORKER_TOKEN", "").strip(),
        data_dir=Path(os.getenv("VOVAN_DATA_DIR", "data")),
        logs_dir=Path(os.getenv("VOVAN_LOGS_DIR", "logs")),
        reports_dir=Path(os.getenv("VOVAN_REPORTS_DIR", "reports")),
        dry_run=os.getenv("VOVAN_DRY_RUN", "true").lower() in {"1", "true", "yes"},
    )


def missing_required_keys(settings: Settings) -> list[str]:
    missing: list[str] = []
    if not settings.vladcher_base_url:
        missing.append("VLADCHER_BASE_URL")
    if not settings.vovan_worker_token:
        missing.append("VOVAN_WORKER_TOKEN")
    return missing
