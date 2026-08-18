from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def test_result_explanation_describes_output_without_advising_user():
    source = (WEB / "client-advice-boundary.js").read_text(encoding="utf-8")
    assert "automatizovaný informační výstup" in source
    assert "Nejde o individuální daňové" in source
    assert "doporučení ani určení postupu uživatele" in source
    assert "měli byste" not in source.lower()
    assert "doporučujeme" not in source.lower()
    assert "je nutné" not in source.lower()


def test_advice_boundary_layer_is_loaded_on_guided_client_page():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "/ui-assets/client-advice-boundary.js" in html
    assert html.index("client-polish.js") < html.index("client-advice-boundary.js") < html.index("app.js")


def test_workspace_production_palette_matches_report_family():
    css = (WEB / "workspace-designs.css").read_text(encoding="utf-8")
    for token in ("#1B2A4A", "#E4EAF6", "#FBFAF6", "#F4F5F8", "#E1E0D8", "#EFEDE4"):
        assert token in css
    assert "box-shadow:none!important" in css
    assert 'body[data-design="atlas"] .dashboard-metrics' in css
