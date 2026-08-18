from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "app" / "web"

CLIENT_SURFACES = (
    "index.html",
    "client-polish.js",
    "client-advice-boundary.js",
    "workspace.html",
    "workspace.js",
    "workspace-report-export.js",
)


def test_client_web_does_not_use_recommendatory_instruction_language():
    prohibited = (
        "doporučujeme",
        "doporučujeme vám",
        "měli byste",
        "měla byste",
        "obraťte se na daňového poradce",
        "ověřte s daňovým poradcem",
    )
    for filename in CLIENT_SURFACES:
        text = (WEB / filename).read_text(encoding="utf-8").lower()
        for phrase in prohibited:
            assert phrase not in text, f"{phrase!r} found in {filename}"


def test_primary_client_surfaces_state_information_only_boundary():
    guided = (WEB / "index.html").read_text(encoding="utf-8").lower()
    workspace = (WEB / "workspace.html").read_text(encoding="utf-8").lower()

    assert "neposkytuje individuální daňové nebo právní poradenství" in guided
    assert "neurčuje postup uživatele" in guided
    assert "neposkytuje individuální daňové nebo právní poradenství" in workspace


def test_hero_boundary_describes_software_output_not_taxpayer_action():
    boundary = (WEB / "client-advice-boundary.js").read_text(encoding="utf-8").lower()
    assert "zobrazený výsledek je automatizovaný informační výstup" in boundary
    assert "určení postupu uživatele" in boundary
