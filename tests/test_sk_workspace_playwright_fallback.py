from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAYWRIGHT = ROOT / "scripts" / "verify_sk_workspace_playwright.py"
AUTO = ROOT / "scripts" / "verify_sk_workspace_browser_auto.sh"


def test_playwright_fallback_covers_public_release_gate_contract():
    text = PLAYWRIGHT.read_text(encoding="utf-8")

    assert 'dataset.sourceCountry === "CZ"' in text
    assert 'value === "CZK"' in text
    assert "public source-country selector is hidden" in text
    assert "SK is not publicly selectable" in text
    assert "public source-country context exposes CZ only" in text
    assert "unsupported SK public context fails closed" in text
    assert "Unsupported public source country: SK" in text
    assert "public source country remains CZ" in text
    assert "public currency remains CZK" in text
    assert "BROWSER_SMOKE_OK" in text


def test_playwright_fallback_uses_bounded_dom_readiness_not_networkidle():
    text = PLAYWRIGHT.read_text(encoding="utf-8")

    assert 'wait_until="domcontentloaded"' in text
    assert "wait_for_workspace_ready(page)" in text
    assert "NAVIGATION_TIMEOUT_MS = 10_000" in text
    assert "DOM_READY_TIMEOUT_MS = 10_000" in text
    assert "ACTION_TIMEOUT_MS = 5_000" in text
    assert 'wait_until="networkidle"' not in text
    assert "browser.close()" in text
    assert "server.terminate()" in text


def test_auto_browser_launcher_prefers_agent_browser_then_playwright():
    text = AUTO.read_text(encoding="utf-8")

    assert "command -v agent-browser" in text
    assert "verify_sk_workspace_browser.sh" in text
    assert "verify_sk_workspace_playwright.py" in text
