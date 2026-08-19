from taxtreat.services.reporting.html_localization import localize_report_html


def test_czech_report_html_is_byte_preserved():
    html = "Česká srážková daň · v České republice · zákona č. 586/1992 Sb., o daních z příjmů"
    report = {"scope": {"source_country": "CZ"}}

    assert localize_report_html(html, report) == html


def test_slovak_report_html_replaces_czech_legal_and_compliance_copy():
    html = (
        "Česká srážková daň · v České republice · "
        "zákona č. 586/1992 Sb., o daních z příjmů · "
        "Odvod srážkové daně · "
        "Oznámení o příjmech plynoucích do zahraničí (§ 38da ZDP) · "
        "Vazba příjmu ke stálé provozovně v ČR"
    )
    report = {"scope": {"source_country": "SK"}}

    localized = localize_report_html(html, report)

    assert "Slovenská zrážková daň" in localized
    assert "v Slovenskej republike" in localized
    assert "zákona č. 595/2003 Z. z. o dani z príjmov" in localized
    assert "Odvod zrážkovej dane" in localized
    assert "Oznámenie o zrazení a odvedení dane (§ 43 ods. 11)" in localized
    assert "Väzba príjmu na stálu prevádzkareň v SR" in localized
    assert "Vazba příjmu ke stálé provozovně v SR" not in localized
    assert "586/1992" not in localized
    assert "§ 38da" not in localized


def test_slovak_report_html_does_not_claim_cnb_or_czk_by_copy_localization():
    html = "Slovenská zrážková daň · EUR"
    report = {"scope": {"source_country": "SK"}}

    localized = localize_report_html(html, report)

    assert "CNB" not in localized
    assert "ČNB" not in localized
    assert "CZK" not in localized
