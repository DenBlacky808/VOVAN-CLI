# VOVAN Architecture (MVP)

## Роль ВОВАНА

VOVAN — локальный runtime-worker для OCR-пайплайна, который выполняется на машине оператора (Hackintosh/macOS в текущем MVP).

## Связь с VLADCHER_ru

Главный канал интеграции — HTTP API VLADCHER_ru. VOVAN работает в pull-mode: сам опрашивает API, получает задания, обрабатывает и отправляет результат обратно.

## Live worker flow (one-shot)

`vovan worker --live --once` выполняет следующий пайплайн:

1. `claim_next_job` (Bearer `VOVAN_WORKER_TOKEN`).
2. При `job=None` возвращает `ok/no_job`.
3. `download_job_file` в `VOVAN_DOWNLOAD_DIR`.
4. `run_preflight` локально.
5. `run_placeholder_ocr`.
6. `submit_result` (complete).
7. Если preflight не проходит — `submit_failure`.

## API-клиент и обработка ошибок

Клиент возвращает структурированные ошибки:
- auth/permissions: 401/403;
- missing/conflict: 404/409;
- server-side: 5xx;
- invalid JSON;
- network timeout / URL errors.

Это позволяет worker возвращать machine-readable результат для отчётов и CI smoke.

## Почему pull-mode и API-first

- Не требуются входящие соединения на локальную машину.
- Проще эксплуатация в домашних/локальных сетях.
- API контракт остаётся единым между worker и центральной системой.

## Почему Docker Compose

Docker Compose даёт воспроизводимое окружение запуска CLI/worker на macOS: одинаковые зависимости, единая конфигурация volumes, предсказуемый старт.

## Ограничения GPU в этом PR

- GPU (Radeon RX6800XT) не подключается в macOS Docker в рамках этого MVP.
- ROCm/GPU слой отложен как Linux-only roadmap этап.

## Что не входит в MVP

- Тяжёлый OCR движок.
- Browser Operator / Playwright.
- Локальный web-сервер.
