# VOVAN-CLI

Formerly: VOVAN-OCR-CLI-MVP.

VOVAN-CLI — portable local compute executor: локальный CLI-исполнитель, который запускает вычислительные задачи на машине оператора и возвращает безопасный результат во внешнюю систему.

OCR — первый модуль внутри VOVAN-CLI, а не вся сущность проекта. Terminal worker остаётся **pull-mode bridge** к VLADCHER_ru: сайт создаёт job, VOVAN-CLI сам забирает её, скачивает input, обрабатывает локально и отправляет complete/fail result.

## Что это

- Локальный вычислительный CLI-исполнитель для задач, которые должны выполняться рядом с приватными файлами и локальными инструментами.
- Первая целевая среда: macOS Intel / Hackintosh.
- Linux и Docker — поддерживаемое/планируемое направление для переносимого core runtime.
- Не веб-сайт, не macOS app и не замена VLADCHER_ru.
- Без входящих соединений.
- OCR pipeline — первый модуль. Worker OCR по умолчанию остаётся placeholder.
- Локальный file OCR CLI уже умеет извлекать реальный текст из PNG/JPG/JPEG/PDF через Tesseract.
- Engine worker переключается через `VOVAN_OCR_ENGINE` (`placeholder` по умолчанию, `tesseract` для smoke/checkpoint).
- Runtime и bridge границы описаны в `docs/VOVAN_CLI_RUNTIME_BOUNDARY_RU.md` и `docs/VOVAN_SITE_BRIDGE_BOUNDARY_RU.md`.

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

## Terminal worker pipeline

`vovan worker` запускает локальный terminal worker в pull-mode и служит bridge к VLADCHER_ru:

```bash
vovan worker --live
```

Для одного прохода без daemon-loop:

```bash
vovan worker --live --once
```

Worker использует `VLADCHER_BASE_URL` и `VOVAN_WORKER_TOKEN`, но не печатает их значения. Цикл polling переживает временные API/network ошибки, пишет короткий JSON status log, ждёт `VOVAN_WORKER_POLL_SECONDS` между обычными попытками и `VOVAN_WORKER_ERROR_BACKOFF_SECONDS` после ошибок. `Ctrl+C` завершает daemon чисто.

PDF job в worker сейчас обрабатывается ограниченным безопасным маршрутом:

- проверяется PDF header/структура;
- text layer извлекается через лёгкую зависимость `pypdf`, если он есть;
- scanned/no-text PDF возвращает controlled placeholder без raw content;
- worker не запускает `pdftoppm`, `tesseract`, `ocrmypdf` или batch OCR для PDF job в этом pipeline.

Расширенный result payload остаётся совместим с текущим complete/fail контрактом: worker отправляет `result_text`/`error_message` и безопасные поля `extracted_text`, `page_count`, `has_text_layer`, `processing_warnings`, `worker_result_summary` или `safe_error`.

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
- `VOVAN_WORKER_POLL_SECONDS=5`
- `VOVAN_WORKER_ERROR_BACKOFF_SECONDS=15`

If `pdftoppm` is not available, PDF OCR with `tesseract` safely falls back to placeholder with `engine_warning`.

Note: the terminal worker PDF route intentionally does not use the PDF→PNG/Tesseract stack. That stack is only for the separate local file OCR CLI path and can be wired into worker PDF processing in a later focused PR.

## Docker Compose

```bash
docker compose up --build vovan-worker
```

См. `docs/runbook.md`, `docs/architecture.md`, `docs/VOVAN_CLI_RUNTIME_BOUNDARY_RU.md`, `docs/VOVAN_SITE_BRIDGE_BOUNDARY_RU.md`, `docs/VOVAN_SAFETY_LAYER_RU.md` и smoke-checkpoint'ы `docs/smoke/tesseract_image_smoke.md`, `docs/smoke/tesseract_rus_eng_smoke.md`.

## Live API контракт (VLADCHER_ru worker API)

VOVAN worker использует только следующие endpoint'ы:

- `GET /api/vovan/ocr/jobs/next/`
- `GET /api/vovan/ocr/jobs/<job_id>/download/`
- `POST /api/vovan/ocr/jobs/<job_id>/complete/`
- `POST /api/vovan/ocr/jobs/<job_id>/fail/`
- `GET /api/vovan/ocr/jobs/<job_id>/status/`
