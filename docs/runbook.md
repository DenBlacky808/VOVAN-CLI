# VOVAN Runbook (MVP)

## 1) Подготовка

```bash
cp .env.example .env
```

Заполните:
- `VLADCHER_BASE_URL`
- `VOVAN_WORKER_TOKEN`
- `VOVAN_DRY_RUN`

Опционально для terminal daemon:
- `VOVAN_WORKER_POLL_SECONDS`
- `VOVAN_WORKER_ERROR_BACKOFF_SECONDS`

Не записывайте реальные token/env значения в runbook, issue, PR или логи.

## 2) Установка

```bash
make install
```

## 3) Проверка окружения

```bash
make doctor
```

## 4) Preflight файла

```bash
make preflight SAMPLE=./data/sample.txt
```

## 5) Local file OCR (real Tesseract text)

Установка macOS/Hackintosh:

```bash
brew install tesseract poppler
python3 -m pip install -e ".[dev]"
```

Smoke test для PNG/JPG/JPEG:

```bash
python3 -m vovan.local_ocr /path/to/file.png
```

Альтернативный entrypoint после установки:

```bash
vovan-ocr-file /path/to/file.jpg
```

Smoke test для PDF:

```bash
python3 -m vovan.local_ocr /path/to/file.pdf
```

С языками и DPI:

```bash
vovan-ocr-file --lang rus+eng --pdf-dpi 250 /path/to/file.pdf
```

Поддерживаемые форматы: `.png`, `.jpg`, `.jpeg`, `.pdf`.

Ограничения:
- Если `tesseract` не установлен или не найден в `PATH`, команда завершается non-zero.
- Для PDF нужен Poppler `pdftoppm`; если он не найден в `PATH`, команда завершается non-zero с подсказкой `brew install poppler`.
- PDF конвертируется во временные PNG-страницы, каждая страница OCRится Tesseract, итоговый текст склеивается с разделителями `--- page 1 ---`.
- Если OCR для PNG/JPG/JPEG вернул пустой текст, команда завершается non-zero с явной ошибкой.
- Если OCR для PDF-страницы пустой, разделитель страницы сохраняется, а текст страницы становится `[empty OCR output]`.
- Качество зависит от изображения и установленных language packs.
- Не коммитьте персональные PDF, сканы, скриншоты или локальные OCR-сэмплы. Для тестов используйте только временные/generated fixtures.

## 6) Placeholder OCR

```bash
make ocr SAMPLE=./data/sample.txt
```

## 7) Docker Compose worker

```bash
make docker-worker
```

## 8) Terminal daemon worker

Один live-проход:

```bash
vovan worker --live --once
```

Постоянный polling в терминале:

```bash
vovan worker --live
```

Остановить вручную:

```bash
Ctrl+C
```

Ожидаемый idle log, когда job нет:

```json
{"message": "No job available", "status": "ok", "worker_state": "idle"}
```

Ожидаемый completed PDF MVP result:

```json
{
  "job_id": "<job-id>",
  "status": "completed",
  "extracted_text": "PDF accepted; scanned-page OCR is not enabled in MVP",
  "page_count": 1,
  "has_text_layer": false,
  "processing_warnings": ["No PDF text layer detected; scanned-page OCR is not enabled in MVP."],
  "worker_result_summary": "PDF accepted as scanned/no-text; OCR placeholder returned."
}
```

Ожидаемый controlled failed result:

```json
{
  "job_id": "<job-id>",
  "status": "failed",
  "safe_error": "PDF preflight failed: file is not a readable PDF",
  "processing_warnings": ["File header is not a PDF header."]
}
```

PDF worker MVP:
- text layer извлекается лёгкой зависимостью `pypdf`;
- если `pypdf` не установлен, worker не падает и возвращает safe placeholder/failed result;
- scanned PDF принимается, но page OCR пока не включён;
- `pdftoppm`, `tesseract`, `ocrmypdf` и тяжёлый batch OCR не запускаются worker pipeline в этом PR.

Smoke flow с сайтом:
- VLADCHER_ru создаёт OCR job;
- VOVAN видит job через `GET /api/vovan/ocr/jobs/next/`;
- VOVAN скачивает файл через download endpoint;
- VOVAN определяет PDF/image;
- VOVAN отправляет completed или controlled failed result;
- VLADCHER_ru показывает итоговый status/result.

## 9) Где смотреть артефакты

- Логи: `./logs`
- Отчёты: `./reports`

## 10) API paths (реальный контракт)

Проверьте, что worker ходит в VLADCHER_ru только по следующим путям:

- `GET /api/vovan/ocr/jobs/next/`
- `GET /api/vovan/ocr/jobs/<job_id>/download/`
- `POST /api/vovan/ocr/jobs/<job_id>/complete/` с payload минимум `{"result_text": "..."}`
- `POST /api/vovan/ocr/jobs/<job_id>/fail/` с payload минимум `{"error_message": "..."}`
- `GET /api/vovan/ocr/jobs/<job_id>/status/`

Worker completed payload дополнительно отправляет:
- `job_id`
- `status`
- `extracted_text`
- `page_count`
- `has_text_layer`
- `processing_warnings`
- `worker_result_summary`

Worker failed payload дополнительно отправляет:
- `job_id`
- `status`
- `safe_error`
- `processing_warnings`

Payload не должен содержать локальные абсолютные пути, реальные env-значения, auth headers или traceback с machine-specific diagnostics.
