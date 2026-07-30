from pathlib import Path
import yaml


def test_phase_1_oecd_scope():
    path = Path("knowledge_base/scope/phase_1_oecd.yaml")
    assert path.exists()

    scope = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert scope["payer_countries"] == ["CZ"]
    assert len(scope["recipient_countries"]) == 38
    assert len(set(scope["recipient_countries"])) == 38
    assert scope["income_types"] == ["dividends", "interest", "royalties"]
    assert scope["expected_records"] == 114
    assert "US" in scope["recipient_countries"]
    assert "CZ" in scope["recipient_countries"]
