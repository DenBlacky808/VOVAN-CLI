from __future__ import annotations

import argparse
import json
import platform
import sys

from vovan.config import load_settings, validate_required_env
from vovan.ocr import _is_tesseract_available, list_tesseract_languages, run_ocr
from vovan.preflight import run_preflight
from vovan.report import write_report
from vovan.worker import list_jobs, run_worker, run_worker_loop


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
        "ocr_engine": settings.ocr_engine,
        "tesseract_available": _is_tesseract_available(),
        "tesseract_path": None,
        "tesseract_languages_available": [],
        "tesseract_lang_configured": settings.tesseract_lang,
        "tesseract_lang_available": False,
    }
    if result["tesseract_available"]:
        import shutil

        languages = list_tesseract_languages()
        result["tesseract_path"] = shutil.which("tesseract")
        result["tesseract_languages_available"] = languages
        requested_languages = [token.strip() for token in settings.tesseract_lang.split("+") if token.strip()]
        result["tesseract_lang_available"] = bool(languages) and all(token in languages for token in requested_languages)

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

    result = run_ocr(
        path,
        settings.ocr_engine,
        tesseract_lang=settings.tesseract_lang,
        pdf_max_pages=settings.pdf_max_pages,
        pdf_dpi=settings.pdf_dpi,
    )
    result["ocr_engine"] = result.get("engine")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    write_report(settings, "ocr", {"preflight": preflight, "ocr": result})
    return 0


def cmd_worker(worker_mode: str | None = None, once: bool = False) -> int:
    settings = load_settings()
    if worker_mode == "dry-run":
        settings.dry_run = True
    if worker_mode == "live":
        settings.dry_run = False

    if once:
        result = run_worker(settings)
        result["once"] = True
        if "ocr_engine" not in result:
            result["ocr_engine"] = settings.ocr_engine
        print(json.dumps(result, ensure_ascii=False, indent=2))
        write_report(settings, "worker", result)
        return 0 if result.get("status") == "ok" else 1

    result = run_worker_loop(settings)
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
    mode_group.add_argument("--dry-run", action="store_true")
    mode_group.add_argument("--live", action="store_true")
    p_worker.add_argument("--once", action="store_true")
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
        worker_mode = None
        if getattr(args, "dry_run", False):
            worker_mode = "dry-run"
        if getattr(args, "live", False):
            worker_mode = "live"
        return cmd_worker(worker_mode=worker_mode, once=getattr(args, "once", False))
    if args.command == "jobs":
        return cmd_jobs()
    if args.command == "report":
        return cmd_report()

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
