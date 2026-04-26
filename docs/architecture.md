# VOVAN Architecture (MVP)

## Роль ВОВАНА

VOVAN — локальный runtime-worker для OCR-пайплайна, который выполняется на машине оператора (Hackintosh/macOS в текущем MVP).

## Связь с VLADCHER_ru

Главный канал интеграции — HTTP API VLADCHER_ru. VOVAN работает в pull-mode: сам опрашивает API, получает задания, обрабатывает и отправляет результат обратно.

## Live worker flow (one-shot)

1. `claim_next_job`
2. `download_job_file`
3. local preflight
4. placeholder OCR
5. `submit_result` (или `submit_failure` если preflight не прошёл)

## API client responsibilities

- `Authorization: Bearer <VOVAN_WORKER_TOKEN>` для каждого запроса;
- timeout-конфиг через `VOVAN_REQUEST_TIMEOUT_SECONDS`;
- структурированные ошибки для 401/403/404/409/5xx/network/invalid JSON;
- dry-run без HTTP для локальной проверки пайплайна.

## Почему pull-mode и API-first

- Не требуются входящие соединения на локальную машину.
- Проще эксплуатация в домашних/локальных сетях.
- API контракт остаётся единым между worker и центральной системой.

## Что не входит в MVP

- Реальный OCR движок.
- GPU/ROCm.
- Browser Operator / Playwright.
- Локальный web-сервер.
