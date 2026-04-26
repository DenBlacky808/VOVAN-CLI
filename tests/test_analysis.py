from vovan.analysis import build_document_analysis, classify_document, normalize_ocr_text


def test_normalize_ocr_text_collapses_excessive_whitespace() -> None:
    source = "  Привет\n\n   мир\t\t!  "
    assert normalize_ocr_text(source) == "Привет мир !"


def test_meeting_notice_classified_correctly() -> None:
    text = "Извещение: общее собрание собственников, повестка и очное голосование."
    assert classify_document(text) == "meeting_notice"


def test_voting_ballot_classified_correctly() -> None:
    text = "Бланк решения собственника: голосование по вопросам. Варианты: за, против, воздержался."
    assert classify_document(text) == "voting_ballot"


def test_official_response_classified_correctly() -> None:
    text = "Рассмотрев обращение, сообщаем: на ваше обращение подготовлен ответ."
    assert classify_document(text) == "official_response"


def test_unknown_fallback_works() -> None:
    text = "Случайный текст без устойчивых юридических маркеров и шаблонов."
    assert classify_document(text) == "unknown"


def test_build_document_analysis_contains_required_fields() -> None:
    data = build_document_analysis("Заявление. Прошу рассмотреть вопрос.")
    assert set(data.keys()) == {
        "normalized_text",
        "document_type",
        "document_title",
        "short_summary",
    }
