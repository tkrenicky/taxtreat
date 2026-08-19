from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAYWRIGHT = ROOT / "scripts" / "verify_sk_workspace_playwright.py"
AUTO = ROOT / "scripts" / "verify_sk_workspace_browser_auto.sh"


def test_playwright_fallback_covers_country_round_trip_contract():
    text = PLAYWRIGHT.read_text(encoding="utf-8")

    assert 'dataset.sourceCountry === "CZ"' in text
    assert 'dataset.sourceCountry === "SK"' in text
    assert 'value === "EUR"' in text
    assert 'value === "CZK"' in text
    assert 'runtimeReleased === false' in text
    assert 'OZN4311v26' in text
    assert '75" && a[1] === "225' in text
    assert '101" && a[1] === "303' in text
    assert 'BROWSER_SMOKE_OK' in text


def test_auto_browser_launcher_prefers_agent_browser_then_playwright():
    text = AUTO.read_text(encoding="utf-8")

    assert "command -v agent-browser" in text
    assert "verify_sk_workspace_browser.sh" in text
    assert "verify_sk_workspace_playwright.py" in text
