from vovan.analysis import build_document_analysis, classify_document, normalize_ocr_text


def test_normalize_ocr_text_collapses_whitespace() -> None:
    text = "  Привет\n\n   мир\t\t!  "
    assert normalize_ocr_text(text) == "Привет мир !"


def test_classify_document_meeting_notice() -> None:
    text = "Уведомление: общее собрание. Повестка дня и голосование."
    assert classify_document(text) == "meeting_notice"


def test_classify_document_voting_ballot() -> None:
    text = "Бланк решения: за / против / воздержался"
    assert classify_document(text) == "voting_ballot"


def test_classify_document_official_response() -> None:
    text = "Рассмотрев обращение гражданина, сообщаем следующее."
    assert classify_document(text) == "official_response"


def test_classify_document_unknown_fallback() -> None:
    assert classify_document("какой-то случайный текст без маркеров") == "unknown"


def test_build_document_analysis_contains_required_fields() -> None:
    result = build_document_analysis("  Заявление.   Прошу рассмотреть вопрос. ")
    assert set(result) == {"normalized_text", "document_type", "document_title", "short_summary"}
    assert result["normalized_text"] == "Заявление. Прошу рассмотреть вопрос."
