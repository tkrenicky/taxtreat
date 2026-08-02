from taxtreat.parser.publication import select_treaty_pages


def _notice(number: int, country: str) -> str:
    return (
        f"{number} SDĚLENÍ Ministerstva zahraničních věcí. "
        f"Byla podepsána Smlouva mezi Českou republikou a {country}."
    )


def test_selects_expected_country_from_multi_notice_publication():
    pages = [
        "Obsah publikace",
        _notice(21, "Státem Izrael"),
        "Článek 1\nIzraelská smlouva",
        _notice(22, "Maďarskou republikou"),
        "Článek 1\nMaďarská smlouva",
        "Článek 2\nDaně",
    ]

    result = select_treaty_pages(
        pages,
        expected_country="Maďarsko",
        source_title="21/1995 Sb.",
    )

    assert result.status == "resolved"
    assert result.start_page == 4
    assert result.effective_title == "22/1995 Sb."
    assert result.metadata_mismatch is True
    assert "Maďarská smlouva" in "\n".join(result.pages)
    assert "Izraelská smlouva" not in "\n".join(result.pages)


def test_falls_back_when_publication_has_no_detectable_notice():
    pages = ["Článek 1\nOsoby", "Článek 2\nDaně"]

    result = select_treaty_pages(
        pages,
        expected_country="Rakousko",
        source_title="48/2007 Sb.m.s.",
    )

    assert result.status == "fallback"
    assert result.pages == pages
    assert result.metadata_mismatch is False
