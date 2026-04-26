# Tesseract rus+eng OCR Smoke (Hackintosh checkpoint)

Этот документ фиксирует успешный локальный smoke-тест OCR через Tesseract для PNG-скриншота с русским текстом при настройке `VOVAN_TESSERACT_LANG=rus+eng`.

## Environment checkpoint

- Platform: Hackintosh (local run).
- OCR engine: Tesseract (`VOVAN_OCR_ENGINE=tesseract`).
- OCR languages: `rus+eng` (`VOVAN_TESSERACT_LANG=rus+eng`).

## Commands

Проверка доступных языковых пакетов Tesseract:

```bash
tesseract --list-langs
```

Ожидаемо в списке присутствуют как минимум:

- `rus`
- `eng`

Запуск smoke OCR на PNG-скриншоте с русским текстом:

```bash
VOVAN_OCR_ENGINE=tesseract VOVAN_TESSERACT_LANG=rus+eng python -m vovan.cli ocr "<png screenshot>"
```

## Expected output fields

Успешный результат smoke должен содержать:

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

Следующий безопасный инженерный шаг:

1. Сделать `rus+eng` рекомендуемой локальной настройкой для русскоязычных скриншотов.
2. Сохранить default `eng` для переносимости и предсказуемого поведения на новых окружениях.
3. Следующий engineering step: опциональный image preprocessing / screenshot cleanup перед OCR.

## Explicit non-goals for this checkpoint

- Не меняем runtime code.
- Не меняем worker API.
- Не меняем placeholder default.
- Не добавляем PDF preprocessing.
