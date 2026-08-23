from __future__ import annotations

import json
from pathlib import Path

from taxtreat.tools.extract_sk_mli_notices import (
    PROFILE_PATH,
    _extract_articles,
    _extract_superseded_notices,
    _extract_wht_dates,
    _static_notice_url,
    parse_notice,
)


def _profile():
    return json.loads(Path(PROFILE_PATH).read_text(encoding="utf-8"))


def test_static_notice_url_is_deterministic():
    assert _static_notice_url("410/2018").endswith(
        "/2018/410/vyhlasene_znenie.html"
    )
    assert _static_notice_url("321/2023").endswith(
        "/2023/321/vyhlasene_znenie.html"
    )


def test_extracts_multiple_applied_mli_articles():
    text = (
        "dopĺňa sa znením článku 7 ods. 1 dohovoru; "
        "nahrádza sa znením článku 10 ods. 1, 2 a 3 dohovoru; "
        "uplatní sa znenie článku 13 ods. 2 dohovoru."
    )
    assert _extract_articles(text) == ["7", "10", "13"]


def test_extracts_wht_effective_dates_without_collapsing_multiple_dates():
    text = (
        "v súvislosti s daňami vyberanými zrážkou pri zdroji zo súm "
        "vyplatených nerezidentom, ak skutočnosť nastala 1. januára 2020; "
        "neskôr v súvislosti s daňami vyberanými zrážkou pri zdroji zo súm "
        "vyplatených nerezidentom, ak skutočnosť nastala 1. januára 2024."
    )
    assert _extract_wht_dates(text) == ["2020-01-01", "2024-01-01"]


def test_extracts_superseded_notice():
    text = "K 1. januáru 2024 sa ruší oznámenie č. 255/2019 publikované v Zbierke."
    assert _extract_superseded_notices(text) == ["255/2019"]


def test_parse_notice_preserves_machine_evidence_fail_closed():
    html = """
    <html><body>
      <p>v súvislosti s daňami vyberanými zrážkou pri zdroji zo súm
      vyplatených nerezidentom, ak skutočnosť nastala 1. januára 2019.</p>
      <p>K ustanoveniam sa dopĺňa znenie článku 7 ods. 1 dohovoru.</p>
      <p>K ustanoveniam sa dopĺňa znenie článku 10 ods. 1, 2 a 3 dohovoru.</p>
      <p>Článok sa nahrádza znením článku 13 ods. 2 dohovoru.</p>
    </body></html>
    """
    row = parse_notice(
        recipient_country="AT",
        recipient_country_name="Rakúsko",
        notice="410/2018",
        html=html,
        profile=_profile(),
    )

    assert row["applied_mli_articles"] == ["7", "10", "13"]
    assert row["candidate_result_changing_articles"] == ["7", "10", "13"]
    assert row["wht_effective_dates"] == ["2019-01-01"]
    assert row["substantive_matching_status"] == (
        "machine_extracted_from_bilateral_notice"
    )
    assert row["human_review_status"] == "not_started"
    assert row["approval_eligible"] is False
    assert row["runtime_status"] == "not_released"


def test_parse_notice_keeps_finland_style_supersession_and_split_dates():
    html = """
    <html><body>
      <p>K 1. januáru 2024 sa ruší oznámenie č. 255/2019 publikované v Zbierke.</p>
      <p>v súvislosti s daňami vyberanými zrážkou pri zdroji zo súm
      vyplatených nerezidentom, ak skutočnosť nastala 1. januára 2020.</p>
      <p>Článok sa nahrádza znením článku 9 ods. 4 dohovoru.</p>
      <p>v súvislosti s daňami vyberanými zrážkou pri zdroji zo súm
      vyplatených nerezidentom, ak skutočnosť nastala 1. januára 2024.</p>
      <p>K ustanoveniam sa dopĺňa znenie článku 7 ods. 1 dohovoru.</p>
    </body></html>
    """
    row = parse_notice(
        recipient_country="FI",
        recipient_country_name="Fínsko",
        notice="321/2023",
        html=html,
        profile=_profile(),
    )

    assert row["applied_mli_articles"] == ["7", "9"]
    assert row["candidate_result_changing_articles"] == ["7"]
    assert row["wht_effective_dates"] == ["2020-01-01", "2024-01-01"]
    assert row["superseded_notices"] == ["255/2019"]
