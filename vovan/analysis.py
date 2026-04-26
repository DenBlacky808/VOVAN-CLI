from __future__ import annotations

import re
from typing import Iterable


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_ocr_text(text: str) -> str:
    normalized = _WHITESPACE_RE.sub(" ", text or "")
    return normalized.strip()


def _contains_all(text: str, keywords: Iterable[str]) -> bool:
    return all(keyword in text for keyword in keywords)


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def classify_document(text: str) -> str:
    normalized = normalize_ocr_text(text).lower()
    if not normalized:
        return "unknown"

    if _contains_any(normalized, ["жилкомсервис", "жкс", "управляющая организация"]):
        return "housing_management_document"

    if _contains_any(normalized, ["мчс", "пожар", "эвакуация"]):
        return "mchs_document"

    if _contains_any(normalized, ["почта россии", "рпо", "отправление"]):
        return "postal_document"

    if _contains_any(normalized, ["суд", "исковое заявление", "определение"]):
        return "court_document"

    if _contains_any(normalized, ["договор", "стороны", "предмет договора"]):
        return "contract_or_agreement"

    if _contains_any(normalized, ["администрация", "жилищный комитет"]):
        return "administration_document"

    if _contains_any(normalized, ["рассмотрев обращение", "сообщаем", "на ваше обращение"]):
        return "official_response"

    if _contains_any(normalized, ["общее собрание", "повестка", "голосование"]):
        return "meeting_notice"

    if _contains_any(normalized, ["бланк решения", "воздержался"]) or _contains_all(
        normalized, ["за", "против"]
    ):
        return "voting_ballot"

    if "жалоба" in normalized:
        return "complaint"

    if _contains_any(normalized, ["заявление", "прошу"]):
        return "legal_statement"

    if _contains_any(normalized, ["скриншот", "screenshot"]):
        return "evidence_screenshot"

    return "unknown"


def _build_title(normalized_text: str) -> str:
    if not normalized_text:
        return "Без названия"

    sentence = re.split(r"(?<=[.!?])\s+", normalized_text, maxsplit=1)[0]
    title = sentence[:120].strip(" -—")
    return title or "Без названия"


def _build_summary(normalized_text: str, document_type: str) -> str:
    if not normalized_text:
        return "Краткое содержание недоступно: пустой текст после OCR."

    snippet = normalized_text[:180].rstrip(" ,;:-")
    return f"Тип документа: {document_type}. Фрагмент: {snippet}."


def build_document_analysis(text: str) -> dict:
    normalized_text = normalize_ocr_text(text)
    document_type = classify_document(normalized_text)

    return {
        "normalized_text": normalized_text,
        "document_type": document_type,
        "document_title": _build_title(normalized_text),
        "short_summary": _build_summary(normalized_text, document_type),
    }
