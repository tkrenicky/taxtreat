from __future__ import annotations

import json
from pathlib import Path

import pytest

from taxtreat.services import report_locales
from taxtreat.services.reporting import english_release_localization
from taxtreat.services import web_locale_engine


def test_report_locale_reader_and_resolution(tmp_path, monkeypatch):
    monkeypatch.setattr(report_locales, "_LOCALE_ROOT", tmp_path)

    assert report_locales._read_locale("") is None
    assert report_locales._read_locale("../CZ") is None
    assert report_locales._read_locale("AT") is None

    (tmp_path / "AT.json").write_text("{bad", encoding="utf-8")
    assert report_locales._read_locale("AT") is None

    payload = {
        "rules": {
            "RULE-1": {
                "en": {
                    "text": "Rule-specific English text",
                    "status": "official_treaty_text",
                    "authority": "Authority",
                    "source_url": "https://example.test/rule",
                }
            }
        },
        "articles": {
            "10": {
                "en": {
                    "text": "Article English text",
                    "status": "custom_status",
                    "authority": "",
                    "source_url": "",
                }
            }
        },
    }
    (tmp_path / "AT.json").write_text(json.dumps(payload), encoding="utf-8")

    resolved = report_locales.english_excerpt_for_citation(
        {"rule_id": "RULE-1", "article": 10}, "AT"
    )
    assert resolved["excerpt"] == "Rule-specific English text"
    assert resolved["excerpt_status_label"] == "Official English treaty text"
    assert resolved["excerpt_authority"] == "Authority"

    fallback = report_locales.english_excerpt_for_citation(
        {"rule_id": "MISSING", "article": 10}, "AT"
    )
    assert fallback["excerpt"] == "Article English text"
    assert fallback["excerpt_status_label"] == "Custom Status"
    assert fallback["excerpt_authority"] is None
    assert fallback["excerpt_source_url"] is None

    assert report_locales.english_excerpt_for_citation(
        {"rule_id": "MISSING", "article": 99}, "AT"
    ) is None

    payload["articles"]["11"] = {"en": {"text": "", "status": "official_treaty_text"}}
    payload["articles"]["12"] = {"en": "invalid"}
    (tmp_path / "AT.json").write_text(json.dumps(payload), encoding="utf-8")
    assert report_locales.english_excerpt_for_citation({"article": 11}, "AT") is None
    assert report_locales.english_excerpt_for_citation({"article": 12}, "AT") is None


def test_english_release_localization_branches():
    html = (
        '<html lang="cs">PRÁVNÍ USTANOVENÍ VNITROSTÁTNÍ PRÁVO SMLOUVA '
        'Applied legal basis '
        'Double Tax Treaty between the Czech Republic and Rakousko o zamezení dvojího zdanění</html>'
    )
    assert english_release_localization.finalize_english_report_html(
        html, {"language": "cs", "scope": {"source_country": "CZ"}}
    ) == html
    assert english_release_localization.finalize_english_report_html(
        html, {"language": "en", "scope": {"source_country": "SK"}}
    ) == html

    report = {
        "language": "en",
        "scope": {"source_country": "CZ", "recipient_country": "AT"},
        "result": {"status": "FINAL", "tax_treatment": "domestic_exemption"},
    }
    localized = english_release_localization.finalize_english_report_html(html, report)
    assert 'lang="en"' in localized
    assert "LEGAL PROVISION" in localized
    assert "DOMESTIC LAW" in localized
    assert "TREATY" in localized
    assert "Primary legal basis — domestic exemption" in localized
    assert "Treaty treatment is supplementary." in localized
    assert "Double Tax Treaty between the Czech Republic and AT" in localized

    again = english_release_localization.finalize_english_report_html(localized, report)
    assert again.count("Treaty treatment is supplementary.") == 1


def test_web_locale_translation_helpers(tmp_path):
    web_locale_engine.translation_map.cache_clear()
    pair = tmp_path / web_locale_engine.PAIR_FILES[0]
    pair.write_text(
        'const pairs = [["Český text", "English text"], ["neutral", "ignored"]];',
        encoding="utf-8",
    )

    pairs = web_locale_engine.translation_map(str(tmp_path))
    assert pairs["Český text"] == "English text"
    assert "neutral" not in pairs

    translated = web_locale_engine._translate(
        'Český text cs-CZ Kč localeCompare(countryName(b.iso2), "cs")',
        tmp_path,
    )
    assert "English text" in translated
    assert "en-GB" in translated
    assert "CZK" in translated
    assert 'localeCompare(countryName(b.iso2), "en")' in translated

    assert web_locale_engine._decode_js_string(r"hello\nworld") == "hello\nworld"
    assert web_locale_engine._decode_js_string(r"bad\x") == r"bad\x"

    source = (
        'loadScript("/ui-assets/workspace-header-language-20260821.js");\n'
        'loadScript("/ui-assets/keep.js");\n'
    )
    stripped = web_locale_engine._strip_live_i18n_bootstrap(source)
    assert "workspace-header-language" not in stripped
    assert "keep.js" in stripped
    assert stripped.endswith("\n")


def test_render_workspace_asset_and_document(tmp_path):
    web_locale_engine.translation_map.cache_clear()

    pair = tmp_path / web_locale_engine.PAIR_FILES[0]
    pair.write_text('const p = [["Český text", "English text"]];', encoding="utf-8")

    bootstrap = tmp_path / "workspace-report-export.js"
    bootstrap.write_text(
        'loadScript("/ui-assets/workspace-header-language-20260821.js");\n'
        'loadScript("/ui-assets/keep.js");\n'
        'const a = "Český text Kč";\n'
        'fetch("/analysis/intake", {});\n'
        'if (url.endsWith("/analysis/intake")) {}\n',
        encoding="utf-8",
    )

    assert web_locale_engine.render_workspace_asset(
        tmp_path, "workspace-report-export.js", "cs"
    ).startswith("loadScript")

    rendered = web_locale_engine.render_workspace_asset(
        tmp_path, "workspace-report-export.js", "en"
    )
    assert "workspace-header-language" not in rendered
    assert "/ui-engine/en/keep.js" in rendered
    assert "English text CZK" in rendered
    assert 'fetch("/analysis/intake?lang=en"' in rendered
    assert 'url.includes("/analysis/intake")' in rendered

    (tmp_path / "bad.css").write_text("x", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        web_locale_engine.render_workspace_asset(tmp_path, "bad.css", "en")
    with pytest.raises(FileNotFoundError):
        web_locale_engine.render_workspace_asset(tmp_path, "../outside.js", "en")

    (tmp_path / "workspace.html").write_text(
        '<html lang="cs"><body>Český text<script src="/ui-assets/app.js"></script></body></html>',
        encoding="utf-8",
    )
    cs = web_locale_engine.render_workspace_document(tmp_path, "cs")
    assert 'lang="cs"' in cs
    assert "window.__TAXTREAT_LOCALE__" in cs

    en = web_locale_engine.render_workspace_document(tmp_path, "en")
    assert 'lang="en"' in en
    assert "English text" in en
    assert 'src="/ui-engine/en/app.js"' in en
    assert "window.__TAXTREAT_LOCALE__" in en


def test_localize_intake_response_and_nested_values(tmp_path):
    web_locale_engine.translation_map.cache_clear()
    pair = tmp_path / web_locale_engine.PAIR_FILES[0]
    pair.write_text(
        'const p = [["Český text", "English text"]];',
        encoding="utf-8",
    )

    assert web_locale_engine._translate_payload_value(5, tmp_path) == 5
    nested = web_locale_engine._translate_payload_value(
        {"a": ["Český text", "Neznámý český řetězec"]}, tmp_path
    )
    assert nested["a"][0] == "English text"
    assert nested["a"][1] == "Additional factual condition requires completion or review."

    payload = {
        "intake": {"question": "Český text"},
        "analysis": {"official_excerpt": "Český právní text"},
    }
    assert web_locale_engine.localize_intake_response(payload, tmp_path, "cs") is payload

    localized = web_locale_engine.localize_intake_response(payload, tmp_path, "en")
    assert localized is not payload
    assert localized["intake"]["question"] == "English text"
    assert localized["analysis"] == payload["analysis"]
