from vovan.analysis import build_document_analysis, classify_document, normalize_ocr_text


def test_normalize_ocr_text_collapses_excessive_whitespace() -> None:
    raw = "  Это   тест\n\nс   лишними\tпробелами  "
    assert normalize_ocr_text(raw) == "Это тест с лишними пробелами"


def test_classify_document_meeting_notice() -> None:
    text = "Уведомление: общее собрание собственников. Повестка и голосование прилагаются."
    assert classify_document(text) == "meeting_notice"


def test_classify_document_voting_ballot() -> None:
    text = "Бланк решения: варианты за, против, воздержался."
    assert classify_document(text) == "voting_ballot"


def test_classify_document_official_response() -> None:
    text = "Рассмотрев обращение, сообщаем: на ваше обращение подготовлен ответ."
    assert classify_document(text) == "official_response"


def test_classify_document_unknown_fallback() -> None:
    assert classify_document("Текст без ключевых слов") == "unknown"


def test_build_document_analysis_returns_expected_fields() -> None:
    analysis = build_document_analysis("Общее собрание. Повестка.")
    assert set(analysis.keys()) == {"normalized_text", "document_type", "document_title", "short_summary"}
    assert analysis["document_type"] == "meeting_notice"
