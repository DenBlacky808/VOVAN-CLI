# Tesseract Russian+English OCR Smoke (Hackintosh checkpoint)

Этот документ фиксирует успешный локальный smoke-тест OCR через Tesseract с языковой конфигурацией `VOVAN_TESSERACT_LANG=rus+eng`.

## Environment checkpoint

- Platform: Hackintosh (local run).
- OCR engine: Tesseract.
- Language packs: `rus` и `eng` установлены.

## Commands

Проверка доступных языков Tesseract:

```bash
tesseract --list-langs
```

Ожидаемо в списке присутствуют `rus` и `eng`.

Smoke-команда для PNG screenshot с русским текстом:

```bash
VOVAN_OCR_ENGINE=tesseract VOVAN_TESSERACT_LANG=rus+eng python -m vovan.cli ocr "<png screenshot>"
```

## Expected output fields

В успешном результате должны подтверждаться следующие поля:

- `status=completed`
- `engine_requested=tesseract`
- `engine=tesseract`
- `ocr_engine=tesseract`
- `result_text` содержит читаемый русский текст

## Known limitations

- OCR всё ещё зависит от качества screenshot/изображения.
- URL и UI-текст могут содержать небольшие ошибки распознавания.
- PDF preprocessing всё ещё не реализован.

## NEXT

- Сделать `rus+eng` рекомендуемой локальной настройкой для русскоязычных screenshot.
- Сохранить `eng` как default для portability.
- Следующий инженерный шаг: optional image preprocessing / screenshot cleanup.

## Explicit non-goals for this checkpoint

- Не меняем runtime code.
- Не меняем worker API.
- Не меняем placeholder default.
- Не добавляем PDF preprocessing.
