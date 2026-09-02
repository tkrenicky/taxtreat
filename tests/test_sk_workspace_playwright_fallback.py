from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAYWRIGHT = ROOT / "scripts" / "verify_sk_workspace_playwright.py"
AUTO = ROOT / "scripts" / "verify_sk_workspace_browser_auto.sh"


def test_playwright_fallback_covers_released_sk_public_contract():
    text = PLAYWRIGHT.read_text(encoding="utf-8")

    assert 'select_option("SK")' in text
    assert "document.body.dataset.sourceCountry === 'SK'" in text
    assert 'context["runtimeReleased"] is True' in text
    assert 'context["baseCurrency"] == "EUR"' in text
    assert 'submitted["source_country"] == "SK"' in text
    assert 'page.reload(wait_until="domcontentloaded")' in text
    assert "SK_WORKSPACE_BROWSER_OK" in text


def test_playwright_fallback_uses_bounded_dom_readiness_not_networkidle():
    text = PLAYWRIGHT.read_text(encoding="utf-8")

    assert 'wait_until="domcontentloaded"' in text
    assert "page.wait_for_function" in text
    assert "page.set_default_timeout(10_000)" in text
    assert "page.set_default_navigation_timeout(10_000)" in text
    assert 'wait_until="networkidle"' not in text
    assert "browser.close()" in text
    assert "server.terminate()" in text


def test_auto_browser_launcher_prefers_agent_browser_then_playwright():
    text = AUTO.read_text(encoding="utf-8")

    assert "command -v agent-browser" in text
    assert "verify_sk_workspace_browser.sh" in text
    assert "verify_sk_workspace_playwright.py" in text
