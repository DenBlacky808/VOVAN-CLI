from __future__ import annotations

import json
import platform
from pathlib import Path

from .config import load_settings, missing_required_keys
from .ocr import run_ocr_placeholder
from .preflight import run_preflight
from .report import write_report
from .worker import run_worker, worker_result_to_dict


def _doctor_payload() -> dict:
    settings = load_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)

    missing = missing_required_keys(settings)
    payload = {
        "python_version": platform.python_version(),
        "missing_env": missing,
        "data_dir": str(settings.data_dir),
        "logs_dir": str(settings.logs_dir),
        "reports_dir": str(settings.reports_dir),
        "ready": len(missing) == 0,
    }
    return payload


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="vovan", description="VOVAN OCR CLI MVP")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check local runtime readiness")

    p_preflight = sub.add_parser("preflight", help="Validate local file before OCR")
    p_preflight.add_argument("path", type=str)

    p_ocr = sub.add_parser("ocr", help="Run placeholder OCR")
    p_ocr.add_argument("path", type=str)

    sub.add_parser("worker", help="Run pull worker placeholder")
    sub.add_parser("jobs", help="List jobs placeholder")
    sub.add_parser("report", help="Write report from doctor payload")

    args = parser.parse_args()

    if args.command == "doctor":
        payload = _doctor_payload()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "preflight":
        payload = run_preflight(args.path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "ocr":
        payload = run_ocr_placeholder(args.path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "worker":
        settings = load_settings()
        payload = worker_result_to_dict(run_worker(settings))
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "jobs":
        payload = {
            "status": "dry-run",
            "jobs": [],
            "message": "jobs command placeholder; API contract reserved for pull-mode worker",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "report":
        settings = load_settings()
        payload = _doctor_payload()
        out = write_report("doctor", payload, Path(settings.reports_dir))
        print(json.dumps({"status": "ok", "report": str(out)}, ensure_ascii=False, indent=2))
        return

if __name__ == "__main__":
    main()
