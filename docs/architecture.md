# VOVAN Architecture (MVP)

## Роль ВОВАНА

VOVAN — локальный runtime-worker для OCR-пайплайна, который выполняется на машине оператора (Hackintosh/macOS в текущем MVP).

## Связь с VLADCHER_ru

Главный канал интеграции — HTTP API VLADCHER_ru. VOVAN работает в pull-mode: сам опрашивает API, получает задания, обрабатывает и отправляет результат обратно.

Текущий worker-контракт: `GET /api/vovan/ocr/jobs/next/`, `GET /api/vovan/ocr/jobs/<job_id>/download/`, `POST /api/vovan/ocr/jobs/<job_id>/complete/`, `POST /api/vovan/ocr/jobs/<job_id>/fail/`, `GET /api/vovan/ocr/jobs/<job_id>/status/`.

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
