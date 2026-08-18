from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def test_client_page_uses_single_informational_notice_and_no_marketing_metrics():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "project-metrics" not in html
    assert html.count('class="notice"') == 1
    assert "Právní stav ke dni 12. 8. 2026" in html
    assert "stav použitého datasetu" not in html


def test_client_page_keeps_tax_advice_boundary_explicit():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "Neposkytuje individuální daňové nebo právní poradenství" in html
    assert "neurčuje postup uživatele" in html
    assert "nejde o individuální daňové nebo právní posouzení" in html.lower()
    assert "doporučujeme" not in html.lower()


def test_client_result_has_answer_first_sections_and_report_action():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    for element_id in (
        "hero-outcome",
        "transaction-facts",
        "assumption-items",
        "calculation-summary",
        "legal-basis-content",
        "deadline-items",
        "documentation-items",
        "report-button",
    ):
        assert f'id="{element_id}"' in html
    assert "Zobrazit klientský report" in html


def test_hidden_attribute_always_wins_over_component_display_rules():
    css = (WEB / "client-polish.css").read_text(encoding="utf-8")
    assert "[hidden] { display: none !important; }" in css
    assert ".empty-state[hidden] { display: none !important; }" in css


def test_result_wording_is_conditional_informational_not_recommendatory():
    javascript = (WEB / "client-polish.js").read_text(encoding="utf-8")
    assert "Jde o informační výstup" in javascript
    assert "nikoli o doporučení k postupu" in javascript
    assert "nepředstavuje individuální daňové posouzení ani doporučení" in javascript
    assert "doporučujeme" not in javascript.lower()


def test_client_layer_reuses_canonical_report_endpoint_instead_of_legal_logic():
    javascript = (WEB / "client-polish.js").read_text(encoding="utf-8")
    assert 'originalFetch("/analysis/report"' in javascript
    assert "selected_rule_id" in javascript
    assert "official_sources" in javascript
    # The presentation layer must not contain country-specific treaty conclusions.
    assert "Rakouskem" not in javascript
    assert "čl. 10" not in javascript
