from __future__ import annotations

import re
from collections.abc import Iterable


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_ocr_text(text: str) -> str:
    """Normalize OCR text for robust keyword matching.

    Keeps original casing/punctuation semantics mostly intact while collapsing
    excessive whitespace and trimming edges.
    """
    return _WHITESPACE_RE.sub(" ", text).strip()


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def classify_document(text: str) -> str:
    normalized = normalize_ocr_text(text).lower()

    if not normalized:
        return "unknown"

    if _contains_any(normalized, ("жилкомсервис", " жкс", "управляющая организация")):
        return "housing_management_document"

    if _contains_any(normalized, ("мчс", "пожар", "эвакуац")):
        return "mchs_document"

    if _contains_any(normalized, ("почта россии", "рпо", "почтовое отправление", "трек-номер", "отправление")):
        return "postal_document"

    if _contains_any(normalized, ("исковое заявление", "определение суда", "решение суда", "суд ", " арбитраж")):
        return "court_document"

    if _contains_any(normalized, ("договор", "стороны", "предмет договора", "соглашение")):
        return "contract_or_agreement"

    if _contains_any(normalized, ("бланк решения", "за", "против", "воздержался")) and (
        "голос" in normalized or "собра" in normalized
    ):
        return "voting_ballot"

    if _contains_any(normalized, ("общее собрание", "повестка", "голосование")):
        return "meeting_notice"

    if _contains_any(normalized, ("рассмотрев обращение", "сообщаем", "на ваше обращение")):
        return "official_response"

    if "жалоба" in normalized:
        return "complaint"

    if _contains_any(normalized, ("заявление", "прошу")):
        return "legal_statement"

    if _contains_any(normalized, ("администрация", "жилищный комитет")):
        return "administration_document"

    if _contains_any(normalized, ("скриншот", "screen", "screenshot", "переписка", "whatsapp", "telegram")):
        return "evidence_screenshot"

    return "unknown"


def _build_title(normalized: str, document_type: str) -> str:
    if not normalized:
        return "Без названия"

    first_sentence = re.split(r"[.!?]\s+", normalized, maxsplit=1)[0].strip(" -:;")
    if first_sentence:
        return first_sentence[:120]

    fallback = normalized[:120].strip()
    if fallback:
        return fallback

    return document_type


def _build_short_summary(normalized: str, document_type: str) -> str:
    if not normalized:
        return "Текст не распознан или пуст."

    snippets = [segment.strip() for segment in re.split(r"[.!?]", normalized) if segment.strip()]
    joined = ". ".join(snippets[:2])
    if len(joined) > 220:
        joined = f"{joined[:217].rstrip()}..."

    return f"Тип: {document_type}. {joined}" if joined else f"Тип: {document_type}."


def build_document_analysis(text: str) -> dict:
    normalized = normalize_ocr_text(text)
    document_type = classify_document(normalized)
    return {
        "normalized_text": normalized,
        "document_type": document_type,
        "document_title": _build_title(normalized, document_type),
        "short_summary": _build_short_summary(normalized, document_type),
    }
