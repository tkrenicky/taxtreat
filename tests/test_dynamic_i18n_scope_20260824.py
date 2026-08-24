from pathlib import Path


SCRIPT = Path("app/web/workspace-canonical-live-i18n-dynamic-20260824.js")


def test_dynamic_i18n_is_scoped_to_known_profile_lines():
    script = SCRIPT.read_text(encoding="utf-8")
    assert "const CS_MARKER" in script
    assert "const EN_MARKER" in script
    assert "if (!CS_MARKER.test(text)) return text;" in script
    assert "if (!EN_MARKER.test(text)) return text;" in script


def test_dynamic_i18n_does_not_add_mutation_observer():
    script = SCRIPT.read_text(encoding="utf-8")
    assert "MutationObserver" not in script


def test_profile_yes_no_and_missing_values_are_bidirectional():
    script = SCRIPT.read_text(encoding="utf-8")
    for token in ["Ano", "Yes", "Ne", "No", "Nevyplněno", "Not provided"]:
        assert token in script
