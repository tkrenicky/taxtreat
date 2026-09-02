from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "scripts" / "verify_sk_workspace_playwright.py"


def test_browser_smoke_covers_cz_sk_cz_round_trip_and_release_gate():
    text = SMOKE.read_text(encoding="utf-8")

    assert 'page.evaluate("document.body.dataset.sourceCountry") == "CZ"' in text
    assert "payer_country" in text
    assert 'select_option("SK")' in text
    assert "document.body.dataset.sourceCountry === 'SK'" in text
    assert 'context["runtimeReleased"] is True' in text
    assert 'get_attribute("aria-disabled") == "false"' in text
    assert 'select_option("demo-cz")' in text
    assert "document.body.dataset.sourceCountry === 'CZ'" in text


def test_browser_smoke_checks_slovak_fx_compliance_and_copy_isolation():
    text = SMOKE.read_text(encoding="utf-8")

    assert 'input_value() == "EUR"' in text
    assert 'source_country"] == "SK"' in text
    assert 'OZN4311v26' in text
    assert '["75", "225"]' in text
    assert "595/2003" in text
    assert "586/1992" in text
    assert 'data-lang="en"' in text
    assert "Slovak withholding tax" in text
