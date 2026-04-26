# Tesseract rus+eng OCR Smoke (Hackintosh checkpoint)

Этот checkpoint фиксирует успешный локальный smoke-тест OCR через Tesseract для русскоязычного скриншота при явной языковой конфигурации `rus+eng`.

## Smoke setup

- Platform: Hackintosh (local run).
- OCR engine: `tesseract`.
- Input: PNG screenshot с русским текстом.
- Language packs installed: `rus`, `eng`.

## Commands used

Проверка установленных языков Tesseract:

```bash
tesseract --list-langs
```

Запуск OCR smoke для русского скриншота:

```bash
VOVAN_OCR_ENGINE=tesseract VOVAN_TESSERACT_LANG=rus+eng python -m vovan.cli ocr "<png screenshot>"
```

## Expected output fields

Успешный результат должен содержать:

- `status=completed`
- `engine_requested=tesseract`
- `engine=tesseract`
- `ocr_engine=tesseract`
- `result_text` содержит читаемый русский текст

## Known limitations

- OCR всё ещё зависит от качества скриншота.
- URL и UI-текст могут содержать небольшие ошибки распознавания.
- PDF preprocessing всё ещё не реализован.

## NEXT

1. Сделать `rus+eng` рекомендуемой локальной настройкой для русскоязычных скриншотов.
2. Сохранить `eng` как default для portability.
3. Следующий инженерный шаг: опциональный image preprocessing / screenshot cleanup.

## Explicit non-goals for this checkpoint

- Не меняем runtime code.
- Не меняем worker API.
- Не меняем placeholder default.
- Не добавляем PDF preprocessing.
