import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "app/web/treaty-excerpt-locales-20260824.json"
COUNTRY_DIR = ROOT / "app/web/treaty-excerpt-locales"
RUNTIME = ROOT / "app/web/workspace-treaty-excerpt-locales-20260824.js"
BOOTSTRAP = ROOT / "app/web/workspace-report-export.js"
AUDIT = ROOT / "scripts/audit_treaty_excerpt_locale_coverage.py"


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


def test_country_split_registry_has_verified_articles_10_11_12():
    expectations = {
        "GB": ("HM Revenue & Customs", "official_synthesised_text"),
        "US": ("Internal Revenue Service / United States Government", "official_treaty_text"),
        "IE": ("Irish Revenue", "official_synthesised_text"),
        "CA": ("Department of Justice Canada", "official_treaty_text"),
        "AU": ("Australian Taxation Office", "official_synthesised_text"),
        "HK": ("Hong Kong Inland Revenue Department", "official_synthesised_text"),
        "NZ": ("New Zealand Legislation / Inland Revenue Department", "official_treaty_text"),
    }
    for country, (authority, status) in expectations.items():
        payload = json.loads((COUNTRY_DIR / f"{country}.json").read_text(encoding="utf-8"))
        assert payload["source_country"] == "CZ"
        assert payload["recipient_country"] == country
        for article in ("10", "11", "12"):
            locale = payload["articles"][article]["en"]
            assert locale["language"] == "en"
            assert locale["status"] == status
            assert locale["authority"] == authority
            assert locale["source_url"].startswith("https://")
            assert locale["text"]


def test_za_my_ph_batch_has_official_decisive_english_excerpts():
    expectations = {
        "ZA": "South African Revenue Service",
        "MY": "Inland Revenue Board of Malaysia",
        "PH": "Bureau of Internal Revenue, Philippines",
    }
    for country, authority in expectations.items():
        payload = json.loads((COUNTRY_DIR / f"{country}.json").read_text(encoding="utf-8"))
        assert payload["source_country"] == "CZ"
        assert payload["recipient_country"] == country
        for article in ("10", "11", "12"):
            locale = payload["articles"][article]["en"]
            assert locale["language"] == "en"
            assert locale["status"].startswith("official_")
            assert locale["authority"] == authority
            assert locale["source_url"].startswith("https://")
            assert locale["text"].startswith(f"Article {article}")
            assert "Decisive treaty wording:" in locale["text"]


def test_austria_royalty_and_new_zealand_interest_have_rule_specific_english_excerpts():
    at = json.loads((COUNTRY_DIR / "AT.json").read_text(encoding="utf-8"))
    nz = json.loads((COUNTRY_DIR / "NZ.json").read_text(encoding="utf-8"))

    for rule_id in ("CZ-AT-ROYALTY-CURRENT-1", "CZ-AT-ROYALTY-CURRENT-2"):
        entry = at["rules"][rule_id]
        assert entry["article"] == "12"
        assert entry["en"]["status"] == "official_synthesised_text"
        assert "Article 12(2)" in entry["en"]["text"]

    assert "Article 12(3)(b)" in at["rules"]["CZ-AT-ROYALTY-CURRENT-1"]["en"]["text"]
    assert "Article 12(3)(a)" in at["rules"]["CZ-AT-ROYALTY-CURRENT-2"]["en"]["text"]

    for rule_id in ("CZ-NZ-INTEREST-CURRENT-1", "CZ-NZ-INTEREST-CURRENT-2"):
        entry = nz["rules"][rule_id]
        assert entry["article"] == "11"
        assert entry["en"]["status"] == "official_treaty_text"
    assert "shall not exceed 10 per cent" in nz["rules"]["CZ-NZ-INTEREST-CURRENT-1"]["en"]["text"]
    assert "shall be exempt from tax" in nz["rules"]["CZ-NZ-INTEREST-CURRENT-2"]["en"]["text"]


def test_remaining_ambiguous_au_gb_us_rules_have_rule_specific_english_excerpts():
    expectations = {
        "AU": ("CZ-AU-INTEREST-CURRENT-2", "11", "shall be exempt from tax"),
        "GB": ("CZ-GB-ROYALTY-CURRENT-1", "12", "shall be taxable only in that other State"),
        "US": ("CZ-US-ROYALTY-CURRENT-1", "12", "may be taxed only in that State"),
    }
    for country, (rule_id, article, decisive_phrase) in expectations.items():
        payload = json.loads((COUNTRY_DIR / f"{country}.json").read_text(encoding="utf-8"))
        entry = payload["rules"][rule_id]
        assert entry["article"] == article
        assert entry["en"]["language"] == "en"
        assert entry["en"]["status"].startswith("official_")
        assert entry["en"]["source_url"].startswith("https://")
        assert decisive_phrase in entry["en"]["text"]


def test_runtime_prefers_resolved_rule_locale_then_article_fallback_and_is_fail_visible():
    script = RUNTIME.read_text(encoding="utf-8")
    assert "countryRegistry?.rules?.[selectedRuleId]" in script
    assert "countryRegistry?.articles?.[String(article)]?.en" in script
    assert "specificity: \"rule\"" in script
    assert "specificity: \"article\"" in script
    assert "COUNTRY_REGISTRY_ROOT" in script
    assert "loadCountryRegistry(country)" in script
    assert "Official English treaty wording is not yet registered" in script
    assert "cs-fallback" in script
    assert "MutationObserver" not in script


def test_runtime_captures_selected_treaty_citation_from_live_and_stored_results():
    script = RUNTIME.read_text(encoding="utf-8")
    assert "let selectedTreatyCitation = null" in script
    assert "function captureAnalysis(analysis)" in script
    assert "analysis?.selected_rule_id || analysis?.candidate_rule_id" in script
    assert "selectedTreatyCitation = selected" in script
    assert "response.clone().json()" in script
    assert "captureAnalysis(body?.analysis)" in script
    assert "function installStoredResultHook()" in script
    assert "workspace.openStoredResult = wrapped" in script
    assert "captureAnalysis(response?.analysis)" in script


def test_article_level_locale_only_highlights_uniquely_resolved_outcome_passage():
    script = RUNTIME.read_text(encoding="utf-8")
    assert "function decisiveArticlePassage(text, citation)" in script
    assert "function ratePattern(rate)" in script
    assert "minimal.length === 1" in script
    assert "taxable only" in script
    assert "exempt from tax" in script
    assert "decisiveArticlePassage(locale.text, selectedTreatyCitation)" in script
    assert 'excerpt.dataset.ttTreatyDecisivePassage = highlighted ? "resolved" : "not-isolated"' in script


def test_rule_specific_locale_is_rendered_as_decisive_passage():
    script = RUNTIME.read_text(encoding="utf-8")
    assert 'specificity === "rule"' in script
    assert 'mark.className = "legal-decisive-passage"' in script
    assert "appendWithMark(excerpt, locale.text, decisive)" in script
    assert "ttTreatyLocaleSpecificity" in script


def test_runtime_can_infer_country_for_stored_result_from_full_jurisdiction_catalog():
    script = RUNTIME.read_text(encoding="utf-8")
    assert 'fetch("/jurisdictions", { cache: "no-store" })' in script
    assert "Array.isArray(payload?.jurisdictions)" in script
    assert "function inferRecipientCountry(jurisdictions)" in script
    assert 'new Intl.DisplayNames(["en"], { type: "region" })' in script
    assert 'new Intl.DisplayNames(["cs"], { type: "region" })' in script
    assert 'String(item?.iso2 || "").toUpperCase()' in script


def test_runtime_restores_original_czech_markup_not_only_text():
    script = RUNTIME.read_text(encoding="utf-8")
    assert "const originalExcerpt = new WeakMap()" in script
    assert "Array.from(excerpt.childNodes).map((node) => node.cloneNode(true))" in script
    assert "function restoreOriginal(excerpt)" in script
    assert "excerpt.replaceChildren(...nodes.map((node) => node.cloneNode(true)))" in script
    assert 'declaredLanguage.startsWith("en")' in script


def test_audit_measures_decisive_outcome_evidence_not_blanket_multi_rate_snippets():
    script = AUDIT.read_text(encoding="utf-8")
    assert "Rules with decisive EN outcome evidence" in script
    assert "Rules without decisive EN outcome evidence" in script
    assert "Rules requiring explicit rule-specific EN disambiguation" in script
    assert "_article_supports_outcome" in script
    assert "_condition_signature" in script
    assert "Rules in materially multi-outcome articles" not in script


def test_runtime_is_loaded_after_i18n_and_before_report_core():
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    dynamic = bootstrap.index("workspace-canonical-live-i18n-dynamic-20260824.js")
    treaty_locale = bootstrap.index("workspace-treaty-excerpt-locales-20260824.js")
    report_core = bootstrap.index("workspace-report-export-core.js")
    assert dynamic < treaty_locale < report_core
