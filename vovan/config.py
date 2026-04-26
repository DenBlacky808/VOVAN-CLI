from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    vladcher_base_url: str
    worker_token: str
    mode: str
    data_dir: Path
    log_dir: Path
    report_dir: Path
    download_dir: Path
    allowed_extensions: set[str]
    max_file_size_mb: int
    dry_run: bool
    request_timeout_seconds: int
    worker_sleep_seconds: int


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_env_file(env_file: str) -> None:
    path = Path(env_file)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_settings(env_file: str = ".env") -> Settings:
    _load_env_file(env_file)

    allowed_extensions = {
        ext.strip().lower()
        for ext in os.getenv("VOVAN_ALLOWED_EXTENSIONS", ".pdf,.png,.jpg,.jpeg,.tiff,.txt").split(",")
        if ext.strip()
    }

    return Settings(
        vladcher_base_url=os.getenv("VLADCHER_BASE_URL", "").strip(),
        worker_token=os.getenv("VOVAN_WORKER_TOKEN", "").strip(),
        mode=os.getenv("VOVAN_MODE", "local").strip(),
        data_dir=Path(os.getenv("VOVAN_DATA_DIR", "./data")),
        log_dir=Path(os.getenv("VOVAN_LOG_DIR", "./logs")),
        report_dir=Path(os.getenv("VOVAN_REPORT_DIR", "./reports")),
        download_dir=Path(os.getenv("VOVAN_DOWNLOAD_DIR", "./data/downloads")),
        allowed_extensions=allowed_extensions,
        max_file_size_mb=int(os.getenv("VOVAN_MAX_FILE_SIZE_MB", "50")),
        dry_run=_to_bool(os.getenv("VOVAN_DRY_RUN", "true")),
        request_timeout_seconds=int(os.getenv("VOVAN_REQUEST_TIMEOUT_SECONDS", "30")),
        worker_sleep_seconds=int(os.getenv("VOVAN_WORKER_SLEEP_SECONDS", "5")),
    )


def validate_required_env(settings: Settings) -> list[str]:
    missing = []
    if not settings.vladcher_base_url:
        missing.append("VLADCHER_BASE_URL")
    if not settings.worker_token:
        missing.append("VOVAN_WORKER_TOKEN")
    return missing
