# VOVAN local PDF worker pipeline

## Scope

This patch hardens the existing local VOVAN worker for terminal pull-mode with VLADCHER_ru:

```text
poll server -> claim/get job -> detect image/pdf -> process safely -> submit completed/failed -> continue polling
```

It does not add `pdftoppm`, `tesseract`, `ocrmypdf`, GUI automation, local AI models, launchd, or system service files to the worker pipeline.

## Entrypoint

The current worker entrypoint is package-based:

- CLI: `vovan worker`
- code: `vovan/worker.py`
- API client: `vovan/api_client.py`

`vovan worker --live` runs a terminal daemon loop. `vovan worker --live --once` performs a single claim/process/submit pass.

## VLADCHER_ru contract

The worker uses the existing endpoints:

- `GET /api/vovan/ocr/jobs/next/`
- `GET /api/vovan/ocr/jobs/<job_id>/download/`
- `POST /api/vovan/ocr/jobs/<job_id>/complete/`
- `POST /api/vovan/ocr/jobs/<job_id>/fail/`
- `GET /api/vovan/ocr/jobs/<job_id>/status/`

For compatibility, completed payloads still include `result_text`, and failed payloads still include `error_message`.

Completed payloads also include:

- `job_id`
- `status`
- `extracted_text`
- `page_count`
- `has_text_layer`
- `processing_warnings`
- `worker_result_summary`

Failed payloads also include:

- `job_id`
- `status`
- `safe_error`
- `processing_warnings`

Payloads must not include local absolute paths, auth headers, env values, or tracebacks with machine-specific details.

## PDF MVP behavior

The PDF route is intentionally lightweight:

- `inspect_pdf(file_path)` checks header and readable structure.
- `extract_pdf_text_if_available(file_path)` extracts text layer with `pypdf` when available.
- `fallback_pdf_ocr_placeholder(file_path)` returns `PDF accepted; scanned-page OCR is not enabled in MVP`.
- `process_pdf_job(job)` returns completed text-layer output, completed scanned-PDF placeholder, or controlled failed payload.
- `sanitize_worker_error(error)` strips local paths and auth-like values.

Scanned-page OCR is deliberately left for the next focused PR. The extension point is the placeholder function, where `pdftoppm + tesseract` can later be wired without changing the worker polling/API structure.

## Daemon behavior

The loop:

- logs compact JSON events without secrets;
- treats empty queue as idle and keeps polling;
- catches per-iteration exceptions;
- backs off after temporary errors;
- exits cleanly on `Ctrl+C`.

Configuration:

- `VOVAN_WORKER_POLL_SECONDS`
- `VOVAN_WORKER_ERROR_BACKOFF_SECONDS`

## Smoke checklist

1. Start with `vovan worker --live --once` to verify env and API contract.
2. Run `vovan worker --live` for terminal daemon polling.
3. Create a PDF job on VLADCHER_ru.
4. Confirm VOVAN claims/downloads it.
5. Confirm PDF text-layer jobs return extracted text.
6. Confirm scanned/no-text PDFs return the controlled MVP placeholder.
7. Confirm invalid PDFs return controlled failed payloads with `safe_error`.
