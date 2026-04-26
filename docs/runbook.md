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

## 5) Placeholder OCR

```bash
make ocr SAMPLE=./data/sample.txt
```

## 6) Worker one-shot smoke

```bash
python3 -m vovan.cli worker --dry-run --once
python3 -m vovan.cli worker --live --once
```

## 7) Где смотреть артефакты

- Логи: `./logs`
- Отчёты: `./reports`
- Загрузки job-файлов: `./data/downloads`
