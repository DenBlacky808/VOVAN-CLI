# VOVAN OCR CLI MVP

Локальный backend-worker CLI для VOVAN OCR в режиме **pull-mode** c интеграцией с HTTP API VLADCHER_ru.

## Что это

- Локальный worker (macOS/Hackintosh first, Linux later).
- Не веб-сайт, не замена VLADCHER_ru.
- Без входящих соединений.
- Worker OCR по умолчанию остаётся placeholder.
- Локальный file OCR CLI уже умеет извлекать реальный текст из PNG/JPG/JPEG/PDF через Tesseract.
- Engine worker переключается через `VOVAN_OCR_ENGINE` (`placeholder` по умолчанию, `tesseract` для smoke/checkpoint).

## Быстрый старт

```bash
cp .env.example .env
make install
make doctor
make preflight SAMPLE=./data/sample.txt
make ocr SAMPLE=./data/sample.txt
```

## Local file OCR CLI

Самый маленький локальный путь для macOS/Hackintosh: системный Tesseract CLI и Poppler `pdftoppm` без server API.

Install:

```bash
brew install tesseract poppler
python3 -m pip install -e ".[dev]"
```

Image smoke test:

```bash
python3 -m vovan.local_ocr /path/to/file.png
# or, after install:
vovan-ocr-file /path/to/file.jpg
```

PDF smoke test:

```bash
python3 -m vovan.local_ocr /path/to/file.pdf
# optional language and raster DPI:
vovan-ocr-file --lang rus+eng --pdf-dpi 250 /path/to/file.pdf
```

Supported formats:

- `.png`
- `.jpg`
- `.jpeg`
- `.pdf`

Known limitations:

- Requires `tesseract` on `PATH`; missing dependency exits non-zero with an install hint.
- PDF support requires Poppler `pdftoppm` on `PATH`; install it with `brew install poppler`.
- PDF OCR renders pages to temporary PNG images and OCRs each page with Tesseract.
- PDF output is joined with explicit page separators like `--- page 1 ---`.
- Empty image OCR exits non-zero. Empty PDF pages are kept with the page marker and `[empty OCR output]`.
- OCR quality depends on image clarity and installed Tesseract language packs.
- Do not commit personal PDFs, scans, screenshots, or local OCR samples. Use temporary/generated fixtures only.

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
