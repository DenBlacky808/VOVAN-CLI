from __future__ import annotations

import argparse
import json
import platform
import sys

from vovan.config import load_settings, validate_required_env
from vovan.ocr import run_placeholder_ocr
from vovan.preflight import run_preflight
from vovan.report import write_report
from vovan.worker import list_jobs, run_worker


def cmd_doctor() -> int:
    settings = load_settings()
    missing = validate_required_env(settings)

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "python_version": platform.python_version(),
        "python_ok": sys.version_info >= (3, 10),
        "missing_env": missing,
        "data_dir": str(settings.data_dir),
        "data_dir_exists": settings.data_dir.exists(),
        "log_dir": str(settings.log_dir),
        "log_dir_exists": settings.log_dir.exists(),
        "ready": len(missing) == 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    write_report(settings, "doctor", result)
    return 0 if result["ready"] else 1


def cmd_preflight(path: str) -> int:
    settings = load_settings()
    result = run_preflight(path, settings)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    write_report(settings, "preflight", result)
    return 0 if result["suitable_for_ocr"] else 1


def cmd_ocr(path: str) -> int:
    settings = load_settings()
    preflight = run_preflight(path, settings)
    if not preflight["suitable_for_ocr"]:
        print(json.dumps({"status": "error", "message": "File is not suitable for OCR", "preflight": preflight}, ensure_ascii=False, indent=2))
        return 1

    result = run_placeholder_ocr(path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    write_report(settings, "ocr", {"preflight": preflight, "ocr": result})
    return 0


def cmd_worker(worker_live: bool, worker_dry_run: bool, worker_once: bool) -> int:
    settings = load_settings()
    if worker_live:
        settings.dry_run = False
    if worker_dry_run:
        settings.dry_run = True

    result = run_worker(settings, once=worker_once)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    write_report(settings, "worker", result)
    return 0 if result.get("status") == "ok" else 1


def cmd_jobs() -> int:
    settings = load_settings()
    result = list_jobs(settings)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    write_report(settings, "jobs", result)
    return 0


def cmd_report() -> int:
    settings = load_settings()
    result = {"status": "ok", "message": "Report command executed"}
    path = write_report(settings, "manual", result)
    print(json.dumps({"status": "ok", "report_path": str(path)}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vovan")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor")

    p_pre = sub.add_parser("preflight")
    p_pre.add_argument("path")

    p_ocr = sub.add_parser("ocr")
    p_ocr.add_argument("path")

    p_worker = sub.add_parser("worker")
    mode_group = p_worker.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", dest="worker_dry_run")
    mode_group.add_argument("--live", action="store_true", dest="worker_live")
    p_worker.add_argument("--once", action="store_true", dest="worker_once")

    sub.add_parser("jobs")
    sub.add_parser("report")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "doctor":
        return cmd_doctor()
    if args.command == "preflight":
        return cmd_preflight(args.path)
    if args.command == "ocr":
        return cmd_ocr(args.path)
    if args.command == "worker":
        return cmd_worker(
            worker_live=getattr(args, "worker_live", False),
            worker_dry_run=getattr(args, "worker_dry_run", False),
            worker_once=getattr(args, "worker_once", False),
        )
    if args.command == "jobs":
        return cmd_jobs()
    if args.command == "report":
        return cmd_report()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
