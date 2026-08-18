from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"


def test_guided_page_contains_information_only_boundary():
    html = (WEB / "index.html").read_text(encoding="utf-8")

    assert "Neposkytuje individuální daňové nebo právní poradenství" in html
    assert "neurčuje postup uživatele" in html
    assert "doporučujeme" not in html.lower()
    assert "měli byste" not in html.lower()


def test_guided_page_uses_original_application_flow():
    html = (WEB / "index.html").read_text(encoding="utf-8")

    assert "/ui-assets/app.js" in html
    assert "Plátce a příjemce" in html
    assert "Údaje o platbě" in html
    assert 'id="result"' in html


def test_workspace_production_palette_matches_report_family():
    css = (WEB / "workspace-designs.css").read_text(encoding="utf-8")

    for token in (
        "#173F39",
        "#2E715E",
        "#E8F0EC",
        "#FFFDF8",
        "#F3F7F4",
        "#DDE3DE",
        "#F3F0E8",
    ):
        assert token in css

    assert "box-shadow:none!important" in css
