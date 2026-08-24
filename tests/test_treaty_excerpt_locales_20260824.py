import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "app/web/treaty-excerpt-locales-20260824.json"
RUNTIME = ROOT / "app/web/workspace-treaty-excerpt-locales-20260824.js"
BOOTSTRAP = ROOT / "app/web/workspace-report-export.js"


def test_treaty_locale_registry_has_versioned_data_shape():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["source_country"] == "CZ"
    assert isinstance(payload["entries"], dict)


def test_austria_articles_10_11_12_use_official_english_source():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for article in ("10", "11", "12"):
        locale = payload["entries"]["AT"][article]["en"]
        assert locale["language"] == "en"
        assert locale["status"] == "official_synthesised_text"
        assert locale["authority"] == "Austrian Federal Ministry of Finance"
        assert locale["source_url"].startswith("https://www.bmf.gv.at/")
        assert locale["text"].startswith(f"Article {article}\n")
        assert "Contracting State" in locale["text"]


def test_runtime_is_country_article_language_driven_and_fail_visible():
    script = RUNTIME.read_text(encoding="utf-8")
    assert "registry?.entries?.[country]?.[String(article)]?.en" in script
    assert 'url.endsWith("/analysis/intake")' in script
    assert "recipient_country" in script
    assert "Official English treaty wording is not yet registered" in script
    assert "cs-fallback" in script
    assert "MutationObserver" not in script


def test_runtime_can_infer_country_for_stored_result_without_new_intake():
    script = RUNTIME.read_text(encoding="utf-8")
    assert "function inferRecipientCountry(registry)" in script
    assert 'new Intl.DisplayNames(["en"], { type: "region" })' in script
    assert 'new Intl.DisplayNames(["cs"], { type: "region" })' in script
    assert "Object.keys(registry?.entries || {})" in script


def test_runtime_restores_original_czech_excerpt_on_language_switch_back():
    script = RUNTIME.read_text(encoding="utf-8")
    assert "const originalExcerpt = new WeakMap()" in script
    assert "originalExcerpt.get(excerpt)" in script
    assert 'excerpt.setAttribute("lang", "cs")' in script


def test_runtime_is_loaded_after_i18n_and_before_report_core():
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    dynamic = bootstrap.index("workspace-canonical-live-i18n-dynamic-20260824.js")
    treaty_locale = bootstrap.index("workspace-treaty-excerpt-locales-20260824.js")
    report_core = bootstrap.index("workspace-report-export-core.js")
    assert dynamic < treaty_locale < report_core
