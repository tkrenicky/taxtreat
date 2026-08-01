from taxtreat.validation.document_identity import (
    country_aliases,
    normalize_legal_text,
    publication_reference,
    validate_treaty_identity,
)


def _treaty_text(counterparty: str, reference: str = "22 / 1995") -> str:
    return (
        f"Sbírka zákonů č. {reference}. "
        "SMLOUVA mezi Českou republikou a "
        f"{counterparty} o zamezení dvojímu zdanění. "
        "Článek 1 Osoby, na které se smlouva vztahuje. "
        "Článek 2 Daně, na které se smlouva vztahuje."
    )


def test_normalization_handles_diacritics_ocr_and_line_breaks():
    assert normalize_legal_text("skutečný vlastnõk\nThaj-\nské království") == (
        "skutecny vlastnik thajske kralovstvi"
    )


def test_aliases_are_derived_from_registry_label():
    aliases = country_aliases("USA (Spojené státy americké)")
    assert "usa spojene staty americke" in aliases
    assert "usa" in aliases
    assert "spojene staty americke" in aliases


def test_publication_reference_is_normalized():
    assert publication_reference("Smlouva 022 / 1995 Sb.") == "22/1995"
    assert publication_reference("Treaty without collection number") is None


def test_validates_exact_counterparty_and_publication_reference():
    result = validate_treaty_identity(
        expected_country="Izrael",
        source_title="21/1995 Sb.",
        text=_treaty_text("Státem Izrael", "21 / 1995"),
    )

    assert result.is_valid
    assert result.matched_method == "exact_alias"
    assert result.publication_reference_found is True
    assert result.warnings == ()


def test_validates_inflected_country_name_without_country_specific_aliases():
    result = validate_treaty_identity(
        expected_country="Maďarsko",
        source_title="22/1995 Sb.",
        text=_treaty_text("Maďarskou republikou"),
    )

    assert result.is_valid
    assert result.matched_method == "country_root"


def test_validates_parenthetical_registry_alias():
    result = validate_treaty_identity(
        expected_country="USA (Spojené státy americké)",
        text=_treaty_text("Spojenými státy americkými"),
    )

    assert result.is_valid


def test_rejects_document_for_a_different_counterparty():
    result = validate_treaty_identity(
        expected_country="Maďarsko",
        source_title="21/1995 Sb.",
        text=_treaty_text("Státem Izrael", "21 / 1995"),
    )

    assert not result.is_valid
    assert result.status == "rejected"
    assert result.reason == "counterparty_not_found"


def test_missing_publication_reference_is_auditable_warning_not_false_rejection():
    result = validate_treaty_identity(
        expected_country="Rusko",
        source_title="278/1997 Sb.",
        text=_treaty_text("Ruskou federací", "999 / 1999"),
    )

    assert result.is_valid
    assert result.publication_reference_found is False
    assert result.warnings == ("publication_reference_not_found",)


def test_rejects_empty_or_unusable_extraction():
    result = validate_treaty_identity(expected_country="Rakousko", text="")

    assert not result.is_valid
    assert result.reason == "insufficient_text"


def test_validates_moldavia_registry_name_against_treaty_adjective():
    result = validate_treaty_identity(
        expected_country="Moldávie",
        source_title="88/2000 Sb.m.s.",
        text=_treaty_text("Moldavskou republikou", "88 / 2000"),
    )

    assert result.is_valid
    assert result.matched_method == "country_root"


def test_validates_stan_registry_name_against_republic_adjective():
    result = validate_treaty_identity(
        expected_country="Kyrgyzstán",
        source_title="50/2020 Sb.m.s.",
        text=_treaty_text("Kyrgyzskou republikou", "50 / 2020"),
    )

    assert result.is_valid
    assert result.matched_method == "country_root"


def test_generic_short_adjectival_country_stem():
    result = validate_treaty_identity(
        expected_country="Čína",
        source_title="65/2011 Sb.m.s.",
        text=_treaty_text("Čínskou lidovou republikou", "65 / 2011"),
    )

    assert result.is_valid
    assert result.matched_method == "country_root"
