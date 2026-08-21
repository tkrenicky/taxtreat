from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "app" / "web" / "workspace-report-export.js"
WEB = ROOT / "app" / "web" / "workspace-web-final-20260821.js"


def test_final_web_layer_is_loaded_after_batch1_before_report_core():
    text = LOADER.read_text(encoding="utf-8")
    assert "workspace-ui-batch1-final-20260821.js" in text
    assert "workspace-web-final-20260821.js" in text
    assert "workspace-report-export-core.js" in text
    assert text.index("workspace-ui-batch1-final-20260821.js") < text.index("workspace-web-final-20260821.js")
    assert text.index("workspace-web-final-20260821.js") < text.index("workspace-report-export-core.js")


def test_header_is_intentionally_larger_and_payer_is_compact():
    text = WEB.read_text(encoding="utf-8")
    assert "font-size:18px!important" in text
    assert "min-height:50px!important" in text
    assert "max-width:190px!important" in text
    assert "width:165px!important" in text


def test_language_flags_are_svg_and_refreshed_on_navigation():
    text = WEB.read_text(encoding="utf-8")
    assert "tt-final-flag" in text
    assert "<svg" in text
    assert "refreshLanguageControl" in text
    assert "[data-nav],[data-next-step],[data-flow-step]" in text
    assert "MutationObserver" not in text


def test_section19_result_uses_exemption_not_zero_percent_rate():
    text = WEB.read_text(encoding="utf-8")
    assert "Česká srážková daň se proto neuplatní z důvodu osvobození podle § 19 ZDP" in text
    assert "Primární právní titul: § 19 ZDP" in text
    assert "SZDZ:</strong> pouze sekundární" in text
    assert "Relevantní text § 19 ZDP" in text
    assert 'replaceExact(root, "0 %", en ? "Exempt" : "Osvobozeno")' in text


def test_section19_questions_use_compact_right_side_control():
    text = WEB.read_text(encoding="utf-8")
    assert "grid-template-columns:minmax(0,1fr) minmax(210px,320px)" in text
    assert "grid-template-areas:\"q control\" \"help control\"" in text
