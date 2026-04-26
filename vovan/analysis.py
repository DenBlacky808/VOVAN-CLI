from __future__ import annotations

import re


_WHITESPACE_RE = re.compile(r"\s+")


_KEYWORDS_BY_TYPE: list[tuple[str, tuple[str, ...]]] = [
    ("meeting_notice", ("общее собрание", "повестка", "голосование")),
    ("voting_ballot", ("бланк решения", "за", "против", "воздержался")),
    ("official_response", ("рассмотрев обращение", "сообщаем", "на ваше обращение")),
    ("contract_or_agreement", ("договор", "стороны", "предмет договора")),
    ("court_document", ("суд", "исковое заявление", "определение")),
    ("postal_document", ("почта россии", "рпо", "отправление")),
    ("mchs_document", ("мчс", "пожар", "эвакуация")),
    ("administration_document", ("администрация", "жилищный комитет")),
    ("housing_management_document", ("жилкомсервис", "жкс", "управляющая организация")),
]


def normalize_ocr_text(text: str) -> str:
    normalized = _WHITESPACE_RE.sub(" ", text or "")
    return normalized.strip()


def classify_document(text: str) -> str:
    normalized = normalize_ocr_text(text).lower()
    if not normalized:
        return "unknown"

    if "жалоба" in normalized:
        return "complaint"
    if "заявление" in normalized or "прошу" in normalized:
        return "legal_statement"
    if "скриншот" in normalized or "screenshot" in normalized:
        return "evidence_screenshot"

    for doc_type, keywords in _KEYWORDS_BY_TYPE:
        if any(keyword in normalized for keyword in keywords):
            return doc_type

    return "unknown"


def _build_document_title(normalized_text: str, document_type: str) -> str:
    lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    if lines:
        return lines[0][:120]
    return document_type.replace("_", " ")


def _build_short_summary(normalized_text: str, document_type: str) -> str:
    if not normalized_text:
        return f"Detected document type: {document_type}."
    first_sentence = re.split(r"(?<=[.!?])\s+", normalized_text, maxsplit=1)[0]
    compact = first_sentence.strip()
    if len(compact) > 220:
        compact = compact[:217].rstrip() + "..."
    return compact or f"Detected document type: {document_type}."


def build_document_analysis(text: str) -> dict:
    normalized_text = normalize_ocr_text(text)
    document_type = classify_document(normalized_text)

    return {
        "normalized_text": normalized_text,
        "document_type": document_type,
        "document_title": _build_document_title(normalized_text, document_type),
        "short_summary": _build_short_summary(normalized_text, document_type),
    }
