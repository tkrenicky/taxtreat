from taxtreat.parser.publication import (
    publication_segments,
    resolve_treaty_source,
)


def _notice(number: int, country: str) -> str:
    return (
        f"{number}\nSDĚLENÍ\nMinisterstva zahraničních věcí\n"
        "Ministerstvo zahraničních věcí sděluje, že byla podepsána "
        f"SMLOUVA mezi Českou republikou a {country} o zamezení dvojímu zdanění."
    )


def test_contents_page_is_not_mistaken_for_notice_body():
    pages = [
        (
            "OBSAH 21 Sdělení Ministerstva zahraničních věcí o sjednání smlouvy "
            "s Izraelem 22 Sdělení Ministerstva zahraničních věcí o sjednání "
            "smlouvy s Maďarskem"
        ),
        _notice(21, "Státem Izrael"),
        "Článek 1\nOsoby\nČlánek 10\nDividendy",
        _notice(22, "Maďarskou republikou"),
        "Článek 1\nOsoby\nČlánek 10\nDividendy",
    ]

    segments = publication_segments(pages)
    assert [(item.start_index, item.notice_number) for item in segments] == [
        (1, 21),
        (3, 22),
    ]


def test_resolver_selects_country_segment_and_corrects_registry_number():
    pages = [
        "OBSAH",
        _notice(21, "Státem Izrael"),
        "Článek 1\nOsoby\nČlánek 10\nIzraelská sazba 15 %.",
        _notice(22, "Maďarskou republikou"),
        "Článek 1\nOsoby\nČlánek 10\nMaďarská sazba 10 %.",
    ]

    selected, resolution = resolve_treaty_source(
        pages,
        country="Maďarsko",
        source_title="21/1995 Sb.",
    )

    assert resolution.status == "resolved"
    assert resolution.notice_number == 22
    assert resolution.effective_title == "22/1995 Sb."
    assert resolution.metadata_mismatch is True
    assert "Maďarská sazba" in "\n".join(selected)
    assert "Izraelská sazba" not in "\n".join(selected)


def test_resolver_preserves_whole_document_when_notice_boundaries_are_unknown():
    pages = [
        "SMLOUVA mezi Českou republikou a Rakouskou republikou.",
        "Článek 1\nOsoby\nČlánek 10\nDividendy",
    ]

    selected, resolution = resolve_treaty_source(
        pages,
        country="Rakousko",
        source_title="48/2007 Sb.m.s.",
    )

    assert selected == pages
    assert resolution.status == "fallback"
    assert resolution.method == "whole_document"
    assert resolution.effective_title == "48/2007 Sb.m.s."
