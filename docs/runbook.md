# VOVAN Runbook (MVP)

## 1) Подготовка

```bash
cp .env.example .env
```

Заполните:
- `VLADCHER_BASE_URL`
- `VOVAN_WORKER_TOKEN`
- при необходимости `VOVAN_REQUEST_TIMEOUT_SECONDS`, `VOVAN_WORKER_SLEEP_SECONDS`, `VOVAN_DOWNLOAD_DIR`

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

## 5) Placeholder OCR

```bash
make ocr SAMPLE=./data/sample.txt
```

## 6) Worker one-shot (dry-run)

```bash
vovan worker --dry-run --once
```

## 7) Worker one-shot (live API)

```bash
vovan worker --live --once
```

## 8) Docker Compose worker

```bash
make docker-worker
```

## 9) Где смотреть артефакты

- Логи: `./logs`
- Отчёты: `./reports`
- Загруженные файлы jobs: `./data/downloads`
