# VOVAN Architecture (MVP)

## Роль ВОВАНА

VOVAN — локальный runtime-worker для OCR-пайплайна, который выполняется на машине оператора (Hackintosh/macOS в текущем MVP).

## Связь с VLADCHER_ru

Главный канал интеграции — HTTP API VLADCHER_ru. VOVAN работает в pull-mode: сам опрашивает API, получает задания, обрабатывает и отправляет результат обратно.

### Worker API flow (one-shot)

1. `claim_next_job` (Bearer token).
2. Если job отсутствует — статус `no_job`.
3. `download_job_file` в локальную папку (`VOVAN_DOWNLOAD_DIR`).
4. Локальный `preflight`.
5. Placeholder OCR.
6. При успехе — `submit_result`, при preflight fail — `submit_failure`.

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
