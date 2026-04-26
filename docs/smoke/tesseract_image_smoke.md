# Tesseract image OCR smoke (local checkpoint)

This document captures a successful local smoke run for image OCR with the Tesseract engine.

## Environment checkpoint

- Platform: Hackintosh (local run)
- Tesseract binary path: `/usr/local/bin/tesseract`
- Tesseract version: `5.5.1`

## Availability check

```bash
which tesseract
tesseract --version
```

Expected:
- `which tesseract` returns a valid path (example: `/usr/local/bin/tesseract`).
- `tesseract --version` prints Tesseract version details.

## Supported image extensions

The current image OCR path supports these extensions:

- `.png`
- `.jpg`
- `.jpeg`
- `.tif`
- `.tiff`
- `.bmp`
- `.webp`

## Successful smoke command

```bash
VOVAN_OCR_ENGINE=tesseract python -m vovan.cli ocr "<png screenshot>"
```

## Expected output fields

For a successful Tesseract OCR smoke run, output should confirm:

- `engine_requested=tesseract`
- `engine=tesseract`
- `ocr_engine=tesseract`
- `result_text` is non-empty

## Known limitation

OCR quality depends on:
- installed language packs
- image quality
- font style
- input resolution

## NEXT (safe planning)

- Add `VOVAN_TESSERACT_LANG` environment variable.
- Use `eng` as the default language.
- Allow multi-language values later (for example `rus+eng`).
- Extend `doctor` output to show available Tesseract language packs.

## Non-goals for this checkpoint

- No PDF preprocessing changes.
- No worker API changes.
- No placeholder default behavior changes.
- No heavy dependencies.
