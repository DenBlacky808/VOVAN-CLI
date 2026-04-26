from __future__ import annotations

import re
from collections.abc import Iterable


_WHITESPACE_RE = re.compile(r"\s+")
_LEADING_PAGE_MARKERS_RE = re.compile(r"^(?:-+\s*page\s+\d+\s*-+\s*)+", re.IGNORECASE)


def normalize_ocr_text(text: str) -> str:
    """Normalize OCR text for robust keyword matching.

    Keeps original casing/punctuation semantics mostly intact while collapsing
    excessive whitespace and trimming edges.
    """
    return _WHITESPACE_RE.sub(" ", text).strip()


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _contains_word(text: str, word: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text))


def classify_document(text: str) -> str:
    normalized = normalize_ocr_text(text).lower()

    if not normalized:
        return "unknown"

    if _contains_any(normalized, ("мчс", "пожар", "эвакуац")):
        return "mchs_document"

    if _contains_any(normalized, ("почта россии", "рпо", "почтовое отправление", "трек-номер", "отправление")):
        return "postal_document"

    if _contains_any(normalized, ("исковое заявление", "определение суда", "решение суда", "суд ", " арбитраж")):
        return "court_document"

    strong_meeting_notice_markers = (
        "сообщение",
        "сообщение о проведении",
        "внеочередного общего собрания",
        "общее собрание собственников",
        "повестка дня",
        "форма проведения общего собрания",
    )
    strong_meeting_markers_count = sum(1 for marker in strong_meeting_notice_markers if marker in normalized)
    has_strong_meeting_notice = (
        "сообщение о проведении" in normalized
        or "внеочередного общего собрания" in normalized
        or "общее собрание собственников" in normalized
        or strong_meeting_markers_count >= 2
    )

    if has_strong_meeting_notice:
        return "meeting_notice"

    ballot_headers = (
        "бланк решения",
        "решение собственника",
        "решение собственника помещения",
    )
    ballot_owner_fields = (
        "собственник",
        "паспорт",
        "снилс",
        "подпись",
    )
    has_ballot_header = _contains_any(normalized, ballot_headers)
    owner_fields_count = sum(1 for marker in ballot_owner_fields if marker in normalized)
    has_owner_fields_block = owner_fields_count >= 3

    has_vote_options = all(_contains_word(normalized, option) for option in ("за", "против", "воздержался"))
    ballot_question_markers = len(re.findall(r"(?:вопрос\s*№?\s*\d+|по вопросу\s*№?\s*\d+)", normalized))
    has_repeated_answer_fields = has_vote_options and ballot_question_markers >= 2

    if has_ballot_header or (has_owner_fields_block and has_repeated_answer_fields):
        return "voting_ballot"

    if _contains_any(normalized, ("договор", "стороны", "предмет договора", "соглашение")):
        return "contract_or_agreement"

    if _contains_any(
        normalized,
        (
            "общее собрание",
            "собрание собственников",
            "повестка",
            "голосование",
            "внеочередное общее собрание",
        ),
    ):
        return "meeting_notice"

    if _contains_any(normalized, ("жилкомсервис", " жкс", "управляющая организация")):
        return "housing_management_document"

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

    title_source = _LEADING_PAGE_MARKERS_RE.sub("", normalized).strip()

    first_sentence = re.split(r"[.!?]\s+", title_source, maxsplit=1)[0].strip(" -:;")
    if first_sentence:
        return first_sentence[:120]

    fallback = title_source[:120].strip()
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
