# connect_vovan_cli_to_real_vladcher_worker_api

## Что сделано

- Добавлен live HTTP API client в `vovan/api_client.py` c Bearer авторизацией, one-shot worker endpoint-ами и структурированными ошибками.
- Добавлены env-параметры: `VOVAN_REQUEST_TIMEOUT_SECONDS`, `VOVAN_WORKER_SLEEP_SECONDS`, `VOVAN_DOWNLOAD_DIR`.
- Реализован one-shot flow worker: claim → no_job/download → preflight → placeholder OCR → complete/fail.
- CLI worker расширен флагами `--dry-run`, `--live`, `--once`.
- Обновлены `.env.example`, `README.md`, `docs/runbook.md`, `docs/architecture.md`.
- Обновлён `docs/NEXT_CODEX_TASK.md` на следующий PR: `add_real_cpu_ocr_engine_after_live_api_smoke.md`.
- Добавлены изолированные тесты без доступа к `vladcher.ru`.

## Definition of Done

- `vovan worker --dry-run --once` поддерживается.
- `vovan worker --live --once` реализован.
- `pytest -q` проходит.
- Документация обновлена.
