from vovan.analysis import build_document_analysis, classify_document, normalize_ocr_text


def test_normalize_ocr_text_collapses_excessive_whitespace() -> None:
    source = "  Привет\n\n   мир\t\t!  "
    assert normalize_ocr_text(source) == "Привет мир !"


def test_meeting_notice_classified_correctly() -> None:
    text = "Извещение: общее собрание собственников, повестка и очное голосование."
    assert classify_document(text) == "meeting_notice"


def test_meeting_notice_takes_precedence_over_housing_management_document() -> None:
    text = """
    Сообщение о проведении внеочередного Общего собрания собственников помещений.
    Повестка собрания и порядок голосования указаны ниже.
    Уведомление размещено через Жилкомсервис №1.
    """
    assert classify_document(text) == "meeting_notice"


def test_housing_management_document_without_meeting_markers() -> None:
    text = "Управляющая организация Жилкомсервис №1 сообщает о графике работ в доме."
    assert classify_document(text) == "housing_management_document"


def test_voting_ballot_classified_correctly() -> None:
    text = """
    Бланк решения собственника помещения.
    Собственник: Иванов И.И.
    Паспорт: 1234 567890
    СНИЛС: 123-456-789 00
    Подпись: __________
    Вопрос №1: Утвердить смету?
    За / Против / Воздержался
    Вопрос №2: Выбрать председателя?
    За / Против / Воздержался
    """
    assert classify_document(text) == "voting_ballot"


def test_meeting_notice_not_misclassified_as_ballot_by_vote_words() -> None:
    text = """
    СООБЩЕНИЕ о проведении внеочередного Общего собрания собственников помещений.
    Форма проведения общего собрания: очно-заочная.
    Повестка дня:
    1. Выбор председателя и секретаря собрания.
    2. Утверждение состава счётной комиссии.
    Ниже в тексте встречаются слова: ЗА / ПРОТИВ / ВОЗДЕРЖАЛСЯ.
    """
    assert classify_document(text) == "meeting_notice"


def test_meeting_notice_takes_precedence_over_contract_with_strong_markers() -> None:
    text = """
    Сообщение о проведении внеочередного Общего собрания собственников помещений.
    Повестка и порядок голосования указаны в настоящем уведомлении.
    В приложении также упоминается договор управления.
    Управляющая организация: Жилкомсервис №1.
    """
    assert classify_document(text) == "meeting_notice"


def test_contract_or_agreement_classified_without_strong_meeting_markers() -> None:
    text = "Договор между сторонами. Предмет договора: оказание услуг."
    assert classify_document(text) == "contract_or_agreement"


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


def test_build_document_analysis_title_strips_leading_page_marker() -> None:
    text = "--- PAGE 1 --- Сообщение о проведении внеочередного Общего собрания собственников помещений."
    data = build_document_analysis(text)
    assert not data["document_title"].startswith("PAGE 1")
    assert data["document_title"].startswith("Сообщение")
