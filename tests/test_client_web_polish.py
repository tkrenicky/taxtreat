from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def test_guided_client_page_preserves_core_transaction_flow():
    html = (WEB / "index.html").read_text(encoding="utf-8")

    required = (
        "Krok 1",
        "Plátce a příjemce",
        'name="source_country"',
        'name="recipient_country"',
        'name="recipient_entity_type"',
        "Krok 2",
        "Údaje o platbě",
        'name="income_type"',
        'name="transaction_date"',
        'name="amount"',
        'name="currency"',
        'name="ownership_percent"',
        'name="voting_ownership_percent"',
        'name="acquisition_date"',
        'name="direct_ownership"',
    )

    for item in required:
        assert item in html


def test_guided_client_page_preserves_app_js_contract():
    html = (WEB / "index.html").read_text(encoding="utf-8")

    ids = (
        "case-form",
        "income-type",
        "dividend-fields",
        "fx-fields",
        "form-error",
        "empty-state",
        "result",
        "calculation-card",
        "questions",
        "advisor-items",
        "documents",
        "report-button",
    )

    for element_id in ids:
        assert f'id="{element_id}"' in html

    assert "/ui-assets/app.js" in html


def test_guided_client_page_keeps_information_only_boundary():
    html = (WEB / "index.html").read_text(encoding="utf-8")

    assert "Neposkytuje individuální daňové nebo právní poradenství" in html
    assert "neurčuje postup uživatele" in html
    assert "doporučujeme" not in html.lower()


def test_guided_client_page_keeps_stepwise_help():
    html = (WEB / "index.html").read_text(encoding="utf-8")

    assert "Metodika a nápověda" in html
    assert "Jak výpočet probíhá" in html
    assert "Parametry transakce" in html
    assert "Vypočítat srážkovou daň" in html
