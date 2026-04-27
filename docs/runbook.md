# VOVAN Runbook (MVP)

## 1) Подготовка

```bash
cp .env.example .env
```

Заполните:
- `VLADCHER_BASE_URL`
- `VOVAN_WORKER_TOKEN`

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

## 8) Где смотреть артефакты

- Логи: `./logs`
- Отчёты: `./reports`

## 9) API paths (реальный контракт)

Проверьте, что worker ходит в VLADCHER_ru только по следующим путям:

- `GET /api/vovan/ocr/jobs/next/`
- `GET /api/vovan/ocr/jobs/<job_id>/download/`
- `POST /api/vovan/ocr/jobs/<job_id>/complete/` с payload минимум `{"result_text": "..."}`
- `POST /api/vovan/ocr/jobs/<job_id>/fail/` с payload минимум `{"error_message": "..."}`
- `GET /api/vovan/ocr/jobs/<job_id>/status/`
