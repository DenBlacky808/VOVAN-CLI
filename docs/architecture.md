# VOVAN Architecture (MVP)

## Роль ВОВАНА

VOVAN — локальный runtime-worker для OCR-пайплайна, который выполняется на машине оператора (Hackintosh/macOS в текущем MVP).

## Связь с VLADCHER_ru

Главный канал интеграции — HTTP API VLADCHER_ru. VOVAN работает в pull-mode: сам опрашивает API, получает задания, обрабатывает и отправляет результат обратно.

Worker API flow в этом PR:

1. `claim_next_job` (`POST /api/v1/worker/jobs/claim-next`)
2. `download_job_file` (`GET /api/v1/worker/jobs/{id}/file`)
3. local `preflight`
4. placeholder OCR
5. `submit_result` (`POST /api/v1/worker/jobs/{id}/complete`)
6. при preflight failure: `submit_failure` (`POST /api/v1/worker/jobs/{id}/fail`)

Дополнительно поддерживается `get_job_status` (`GET /api/v1/worker/jobs/{id}`).

## Надёжность API слоя

Клиент возвращает структурированные ошибки для:

- 401/403/404/409
- 5xx
- invalid JSON
- network timeout/connectivity errors

Каждая ошибка включает `category`, `status_code`, `retryable`, `details`.

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
