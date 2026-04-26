# VOVAN OCR CLI MVP

Локальный backend-worker CLI для VOVAN OCR в режиме **pull-mode** c интеграцией с HTTP API VLADCHER_ru.

## Что это

- Локальный worker (macOS/Hackintosh first, Linux later).
- Не веб-сайт, не замена VLADCHER_ru.
- Без входящих соединений.
- Worker OCR по умолчанию остаётся placeholder.
- Локальный image OCR CLI уже умеет извлекать реальный текст через Tesseract.
- Engine worker переключается через `VOVAN_OCR_ENGINE` (`placeholder` по умолчанию, `tesseract` для smoke/checkpoint).

## Быстрый старт

```bash
cp .env.example .env
make install
make doctor
make preflight SAMPLE=./data/sample.txt
make ocr SAMPLE=./data/sample.txt
```

## Local image OCR CLI

Самый маленький локальный путь для macOS/Hackintosh: системный Tesseract CLI без server API и без PDF pipeline.

Install:

```bash
brew install tesseract
python3 -m pip install -e ".[dev]"
```

Smoke test:

```bash
python3 -m vovan.local_ocr /path/to/file.png
# or, after install:
vovan-ocr-file /path/to/file.jpg
```

Supported formats:

- `.png`
- `.jpg`
- `.jpeg`

Known limitations:

- Requires `tesseract` on `PATH`; missing dependency exits non-zero with an install hint.
- Empty OCR output exits non-zero instead of returning placeholder text.
- PDF is intentionally not supported by this CLI.
- OCR quality depends on image clarity and installed Tesseract language packs.

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


## OCR engine settings

- `VOVAN_OCR_ENGINE=placeholder` (default) or `tesseract`
- `VOVAN_TESSERACT_LANG=eng` (supports combined values like `rus+eng`)
- `VOVAN_PDF_MAX_PAGES=3` (for PDF→PNG preprocessing before Tesseract OCR)
- `VOVAN_PDF_DPI=200` (PDF rasterization DPI for `pdftoppm`)

If `pdftoppm` is not available, PDF OCR with `tesseract` safely falls back to placeholder with `engine_warning`.

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
