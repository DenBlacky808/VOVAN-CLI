# VOVAN Runbook (MVP)

## 1) Подготовка

```bash
cp .env.example .env
```

Заполните:
- `VLADCHER_BASE_URL`
- `VOVAN_WORKER_TOKEN`
- (опционально) `VOVAN_REQUEST_TIMEOUT_SECONDS`
- (опционально) `VOVAN_WORKER_SLEEP_SECONDS`
- (опционально) `VOVAN_DOWNLOAD_DIR`

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

## 6) Worker one-shot

Dry-run smoke:

```bash
vovan worker --dry-run --once
```

Live API run:

```bash
vovan worker --live --once
```

Flow: claim next job → download PDF → preflight → placeholder OCR → complete. Если preflight fail, отправляется `submit_failure`.

## 7) Docker Compose worker

```bash
make docker-worker
```

## 8) Где смотреть артефакты

- Downloads: `./data/downloads`
- Логи: `./logs`
- Отчёты: `./reports`
