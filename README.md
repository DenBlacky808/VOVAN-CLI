# VOVAN OCR CLI MVP

Локальный backend-worker CLI для VOVAN OCR в режиме **pull-mode** c интеграцией с HTTP API VLADCHER_ru.

## Что это

- Локальный worker (macOS/Hackintosh first, Linux later).
- Не веб-сайт, не замена VLADCHER_ru.
- Без входящих соединений.
- OCR по умолчанию `placeholder`, а `tesseract` доступен как опциональный engine.
- Для PDF с `tesseract` выполняется безопасный локальный preprocessing через `pdftoppm` (если установлен), затем OCR по страницам.
- Языки Tesseract: `VOVAN_TESSERACT_LANG` (например, `rus+eng`).
- Лимиты PDF preprocessing: `VOVAN_PDF_MAX_PAGES` (по умолчанию `3`) и `VOVAN_PDF_DPI` (по умолчанию `200`).

## Быстрый старт

```bash
cp .env.example .env
make install
make doctor
make preflight SAMPLE=./data/sample.txt
make ocr SAMPLE=./data/sample.txt
```

## CLI команды

- `vovan doctor`
- `vovan preflight <path>`
- `vovan ocr <path>`
- `vovan worker`
- `vovan jobs`
- `vovan report`

## Fallback без install -e

Если entrypoint `vovan` ещё не установлен (например, без `make install`), используйте module mode:

```bash
python3 -m vovan.cli doctor
python3 -m vovan.cli worker
```

## Docker Compose

```bash
docker compose up --build vovan-worker
```

См. `docs/runbook.md`, `docs/architecture.md` и smoke-checkpoint'ы `docs/smoke/tesseract_image_smoke.md`, `docs/smoke/tesseract_rus_eng_smoke.md`.

## Live API контракт (VLADCHER_ru worker API)

VOVAN worker использует только следующие endpoint'ы:

- `GET /api/vovan/ocr/jobs/next/`
- `GET /api/vovan/ocr/jobs/<job_id>/download/`
- `POST /api/vovan/ocr/jobs/<job_id>/complete/`
- `POST /api/vovan/ocr/jobs/<job_id>/fail/`
- `GET /api/vovan/ocr/jobs/<job_id>/status/`
